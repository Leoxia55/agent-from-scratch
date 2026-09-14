"""Agent 入口

整个项目的核心模块，提供了与大模型交互的客户端接口和请求/响应数据结构。
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable, Iterable
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import BaseModel

from .context import (
    AgentResult,
    ExecutionContext,
    PendingToolCall,
    ToolConfirmation,
)
from .llm import LlmClient, LlmRequest, LlmResponse
from .memory import (
    BaseSessionManager,
    TaskMemoryManager,
)
from .sandbox import (
    close_e2b_sandbox,
    create_e2b_sandbox,
    register_sandbox_tools,
)

# skills import
from .skills import (
    SkillInfo,
    discover_skills,
    generate_skills_prompt,
)
from .tools import (
    BaseTool,
    FunctionTool,
    MemoryTool,
    base_e2b_tool,
    execute_python_in_e2b,
    format_tool_definition,
    upload_file_to_e2b,
)
from .types import (
    ContentItem,
    Event,
    Message,
    ToolCall,
    ToolResult,
)

logger = logging.getLogger(__name__)


class Agent:
    """一个具备工具调用，可以循环执行的研究型智能体"""

    def __init__(
        self,
        model: LlmClient | None = None,  # 修改为可选，在run 入口加守卫
        tools: list[BaseTool] | None = None,
        instruction: str = "",
        name: str = "agent",
        max_steps: int = 10,
        description: str = "",
        output_type: type[BaseModel] | None = None,
        # rag and callback
        before_tool_callbacks: list[Callable] | None = None,
        after_tool_callbacks: list[Callable] | None = None,
        # memory
        session_manager: BaseSessionManager | None = None,
        memory_manager: TaskMemoryManager | None = None,
        before_llm_callbacks: list[Callable] | None = None,
        # sandbox and skills
        code_execution: str | None = None,
        skills_path: str | None = None,
        # multi-agents
        sub_agents: list[Agent] | None = None,
        disallow_transfer_to_peers: bool = False,
    ):
        self.model = model
        self.instruction = instruction
        self.name = name
        self.max_steps = max_steps
        self.description = description
        self.output_type = output_type
        self.output_tool_name: str | None = None

        self.session_manager = session_manager
        self.memory_manager = memory_manager
        self.before_tool_callbacks = before_tool_callbacks or []
        self.after_tool_callbacks = after_tool_callbacks or []
        self.before_llm_callbacks = before_llm_callbacks or []
        self.code_execution = code_execution
        self.skills_path = skills_path

        self.sub_agents = sub_agents or []
        self.disallow_transfer_to_peers = disallow_transfer_to_peers
        self.parent: Agent | None = None

        self._sandbox_tools: list[FunctionTool] = []
        self.tools = self._setup_tools(tools or [])

        # Set up sub-agent relationships
        if self.sub_agents:
            self._validate_and_set_sub_agents()

    # --------------------------------------------------------------------------#
    # Core Loop
    # --------------------------------------------------------------------------#
    async def run(
        self,
        user_input: str | None = None,
        context: ExecutionContext | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        tool_confirmations: list[ToolConfirmation] | None = None,
        verbose: bool = False,
    ) -> AgentResult:
        """Execute the agent."""
        if self.model is None:
            raise ValueError("Agent requires a model to run.")
        session = None
        if session_id and self.session_manager:
            session = await self.session_manager.get_or_create(
                session_id, user_id
            )  # 写入user_id

        if context is None:
            context = ExecutionContext(
                session=session,
                session_manager=self.session_manager,
                memory_manager=self.memory_manager,
            )
            if session:
                context.events = list(session.events)
                context.state = dict(session.state)
        elif context.memory_manager is None:
            context.memory_manager = self.memory_manager

        # 恢复待处理工具调用前，搭建代码执行环境.
        if self.code_execution == "e2b" and context.code_env is None:
            await self._setup_code_env(context)

        # 在 E2B 环境就绪后处理工具确认信息.
        if tool_confirmations:
            await self._process_confirmations(context, tool_confirmations)
            pending = [
                PendingToolCall.model_validate(item)
                for item in context.state.get("pending_tool_calls", [])
            ]
            if pending:
                if session and self.session_manager:
                    session.events = list(context.events)
                    session.state = dict(context.state)
                    await self.session_manager.save(session)
                return AgentResult(
                    output=None,
                    context=context,
                    status="pending",
                    pending_tool_calls=pending,
                )

        if user_input:
            user_event = Event(
                execution_id=context.execution_id,
                author="user",
                content=[Message(role="user", content=user_input)],
            )
            context.add_event(user_event)


        terminal = False
        # 循环执行
        try:
            while not context.final_result and context.current_step < self.max_steps:
                result = await self.step(context, verbose=verbose)

                # 检查待处理的工具调用(human-in-the-loop)
                if result and result.status == "pending":
                    if session and self.session_manager:
                        session.events = list(context.events)
                        session.state = dict(context.state)
                        await self.session_manager.save(session)
                    return result

                if context.events:
                    last_event = context.events[-1]
                    if self._is_final_response(last_event):
                        context.final_result = self._extract_final_result(last_event)

                # 检查是否需要转接智能代理
                if context.transfer_to:
                    target_name = context.transfer_to
                    context.transfer_to = None
                    target = self._find_agent(target_name)
                    if target:
                        return await target.run(context=context, verbose=verbose)
            
            terminal = True
            # 保存记忆
            if self.memory_manager:
                try:
                    await self.memory_manager.save(context)
                except Exception as e:
                    logger.warning(f"Failed to save memory:{e}")

            # 保存会话
            if session and self.session_manager:
                session.events = list(context.events)
                session.state = dict(context.state)
                await self.session_manager.save(session)

            return AgentResult(
                output=context.final_result,
                context=context,
                status="complete",
            )
        finally:
            if terminal and context.code_env_owned and context.code_env is not None:
                try:
                    await asyncio.to_thread(close_e2b_sandbox, context.code_env)
                except Exception as exc:
                    logger.warning("Failed to clean up owned E2B sandbox: %s", exc)
                finally:
                    context.code_env = None
                    context.code_env_owned = False

    async def step(
        self,
        context: ExecutionContext,
        verbose: bool = False,
    ) -> AgentResult | None:
        """Perform one think-act cycle"""
        # Prepare what to send to the LLM
        llm_request = await self._prepare_llm_request(context)
        # llm_response = await self.think(llm_request)

        # run before-llm-callbacks
        for callback in self.before_llm_callbacks:
            cb_result = callback(context, llm_request)
            if hasattr(cb_result, "__await__"):
                cb_result = await cb_result
            if cb_result is not None:
                if not isinstance(cb_result, LlmResponse):
                    raise TypeError(
                        "before_llm_callbacks must return LlmResponse or None"
                    )
                # 回调已返回响应，跳过大模型调用
                llm_response = cb_result
                break
        else:  # 如果上面的for 循环没有 llm_response 就 break 或者结束了
            llm_response = await self.think(llm_request)

        if verbose:
            self._log_response(llm_response)

        response_event = Event(
            execution_id=context.execution_id,
            author=self.name,
            content=llm_response.content,
        )
        context.add_event(response_event)

        tool_calls = [c for c in llm_response.content if isinstance(c, ToolCall)]
        if tool_calls:
            result = await self.act(context, tool_calls, verbose=verbose)
            if result and result.status == "pending":
                return result

        context.increment_step()
        return None

    async def think(self, llm_request: LlmRequest) -> LlmResponse:
        """Call the LLM to decide the next action."""
        model = self.model
        if model is None:
            raise ValueError("Agent requires a model to think.")
        return await model.generate(llm_request)

    async def act(
        self,
        context: ExecutionContext,
        tool_calls: list[ToolCall],
        verbose: bool = False,
    ) -> AgentResult | None:
        """Execute the tools requested by the LLM."""
        tools_dict = {tool.name: tool for tool in self.tools}
        results: list[ToolResult] = []
        pending: list[PendingToolCall] = []

        for tool_call in tool_calls:
            if tool_call.name not in tools_dict:
                results.append(
                    ToolResult(
                        tool_call_id=tool_call.tool_call_id,
                        name=tool_call.name,
                        status="error",
                        content=[f"Tool '{tool_call.name}' not found"],
                    )
                )
                continue

            tool_obj = tools_dict[tool_call.name]

            # 检查工具执行是否需要确认 (human-in-the-loop)
            if tool_obj.required_confirmation:
                arguments = tool_call.arguments
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                message = tool_obj.get_confirmation_message(arguments)
                pending.append(
                    PendingToolCall(
                        tool_call=tool_call,
                        confirmation_message=message,
                    )
                )
                continue

            # NEW: before tool callback
            skip = False
            for callback in self.before_tool_callbacks:
                callback_result = callback(context, tool_call)
                if hasattr(callback_result, "__await__"):
                    callback_result = await callback_result
                if callback_result is not None:
                    results.append(
                        ToolResult(
                            tool_call_id=tool_call.tool_call_id,
                            name=tool_call.name,
                            status="error",
                            content=[callback_result],
                        )
                    )
                    skip = True
                    break
            if skip:
                continue

            # 工具调用
            try:
                arguments = tool_call.arguments
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                output = await tool_obj(context, **arguments)

                tool_result = ToolResult(
                    tool_call_id=tool_call.tool_call_id,
                    name=tool_call.name,
                    status="success",
                    content=[output],
                )
            except Exception as e:
                tool_result = ToolResult(
                    tool_call_id=tool_call.tool_call_id,
                    name=tool_call.name,
                    status="error",
                    content=[str(e)],
                )

            # NEW: 工具回调
            for callback in self.after_tool_callbacks:
                callback_result = callback(context, tool_result)
                if hasattr(callback_result, "__await__"):
                    callback_result = await callback_result
                if callback_result is not None:
                    tool_result = callback_result

            if verbose:
                print(
                    f"[{self.name}] Tool Result ({tool_result.name}):\n"
                    + "\n".join(str(item) for item in tool_result.content)
                )
            results.append(tool_result)

        # 如果存在待确认事项，则暂停执行
        if pending:
            # 将待处理调用存储到上下文状态中, 通过 .model_dump() 系列化
            context.state["pending_tool_calls"] = [p.model_dump() for p in pending]
            # still record any result we have
            if results:
                tool_event = Event(
                    execution_id=context.execution_id,
                    author=self.name,
                    content=results,
                )
                context.add_event(tool_event)
            return AgentResult(
                output=None,
                context=context,
                status="pending",
                pending_tool_calls=pending,
            )
        # 记录工具执行结果
        if results:
            tool_event = Event(
                execution_id=context.execution_id,
                author=self.name,
                content=results,
            )
            context.add_event(tool_event)

        return None

    async def _prepare_llm_request(self, context: ExecutionContext) -> LlmRequest:
        """基于当前上下文构建一个大语言模型请求 LlmRequest"""
        flat_contents: list[ContentItem] = []
        for event in context.events:
            flat_contents.extend(event.content)

        instructions: list[str] = []
        if self.instruction:
            instructions.append(self.instruction)
        sandbox_prompt = self._get_sandbox_tools_prompt()
        if sandbox_prompt:
            instructions.append(sandbox_prompt)

        # 如果有可用的技能提示词，则添加。
        if self.skills_path:
            try:
                skills = discover_skills(self.skills_path)
                skills_prompt = generate_skills_prompt(skills)
                if skills_prompt:
                    instructions.append(skills_prompt)
            except Exception:
                pass

        # 向大语言模型开放的筛选工具
        llm_tools = [t for t in self.tools if t.tool_definition is not None]

        # determine tool choice strategy
        if self.output_tool_name:
            tool_choice = "required"
        # elif self.tools:
        elif llm_tools:
            tool_choice = "auto"
        else:
            tool_choice = None

        request = LlmRequest(
            instructions=instructions,
            contents=flat_contents,
            tools=llm_tools,
            tool_choice=tool_choice,
        )


        # 准备 LLM 请求后，会让每个工具处理请求,
        # 这正好触发 MemoryTool.process_llm_request()，实现自动注入
        for tool_obj in self.tools:
            await tool_obj.process_llm_request(context, request)

        return request

    def _is_final_response(self, event: Event) -> bool:
        """检查此事件是否包含最终响应"""
        if self.output_tool_name:
            for item in event.content:
                if (
                    isinstance(item, ToolResult)
                    and item.name == self.output_tool_name
                    and item.status == "success"
                ):
                    return True
            return False

        has_tool_calls = any(isinstance(c, ToolCall) for c in event.content)
        has_tool_results = any(isinstance(c, ToolResult) for c in event.content)
        return not has_tool_calls and not has_tool_results

    def _extract_final_result(self, event: Event) -> Any:
        """Extract the final result from an event."""
        if self.output_tool_name:
            for item in event.content:
                if (
                    isinstance(item, ToolResult)
                    and item.name == self.output_tool_name
                    and item.status == "success"
                    and item.content
                ):
                    return item.content[0]

        for item in event.content:
            if isinstance(item, Message) and item.role == "assistant":
                return item.content
        return None

    def _setup_tools(
        self,
        tools: Iterable[BaseTool | Callable[..., Any]],
    ) -> list[BaseTool]:
        """Prepare the tools list, wrapping plain callables as FunctionTool objects."""
        prepared_tools: list[BaseTool] = []
        for candidate in tools:
            if isinstance(candidate, BaseTool):
                prepared_tools.append(candidate)
            elif callable(candidate):
                prepared_tools.append(FunctionTool(candidate))
            else:
                raise TypeError(
                    "Agent tools must be BaseTool instances or callables, "
                    f"got {type(candidate).__name__}"
                )

        if self.output_type is not None:
            output_schema = self.output_type.model_json_schema()
            output_schema.pop("title", None)
            output_schema.pop("$defs", None)

            tool_definition = format_tool_definition(
                "final_answer",
                "Return the final structured answer matching the required schema.",
                {
                    "type": "object",
                    "properties": {"output": output_schema},
                    "required": ["output"],
                },
            )

            captured_type = self.output_type

            def _parse_output(output) -> Any:
                if isinstance(output, dict):
                    return captured_type.model_validate(output)
                return output

            final_answer_tool = FunctionTool(
                func=_parse_output,
                name="final_answer",
                description="Return the final structured answer matching the required schema.",
                tool_definition=tool_definition,
            )
            prepared_tools.append(final_answer_tool)
            self.output_tool_name = "final_answer"

        # add sandbox-executable tools
        # 1) 过滤无效的沙箱工具
        invalid_sandbox_tools: list[str] = []
        for tool in prepared_tools:
            if not isinstance(tool, FunctionTool) or not tool.sandbox_executable:
                continue
            if self.code_execution != "e2b":
                invalid_sandbox_tools.append(tool.name)
                continue
            self._sandbox_tools.append(tool)

        if invalid_sandbox_tools:
            raise ValueError(
                f"Tools {invalid_sandbox_tools} are marked as sandbox_executable"
                "but code_execution is not enabled."
            )

        # 2) add execution tools
        if self.code_execution == "e2b":
            prepared_tools.extend(
                [execute_python_in_e2b, base_e2b_tool, upload_file_to_e2b]
            )

        # add memory management (skip if the caller already registered one)
        if self.memory_manager and not any(
            tool.name == "recall_memory" for tool in prepared_tools
        ):
            prepared_tools.append(MemoryTool())
        return prepared_tools

    async def prepare_code_env(
        self,
        context: ExecutionContext,
        *,
        caller_owns_sandbox: bool = False,
    ) -> None:
        """Prepare an E2B environment before running with an explicit context.

        ``run`` normally creates and cleans up its own sandbox. Callers that
        need to inspect files after ``run`` returns can prepare the environment
        explicitly and take responsibility for cleanup.
        """
        if self.code_execution != "e2b":
            raise ValueError("An E2B code environment requires code_execution='e2b'.")
        if context.code_env is not None:
            raise ValueError("The execution context already has a code environment.")

        await self._setup_code_env(context)
        context.code_env_owned = not caller_owns_sandbox

    async def _setup_code_env(self, context: ExecutionContext) -> None:
        """Set up E2B sandbox environment and upload configured skills."""
        sandbox = await asyncio.to_thread(
            create_e2b_sandbox, allow_internet_access=True
        )
        try:
            await asyncio.to_thread(
                register_sandbox_tools, sandbox, self._sandbox_tools
            )
            if self.skills_path:
                skills = discover_skills(self.skills_path)
                await asyncio.to_thread(self._upload_skills, sandbox, skills)
        except Exception:
            try:
                await asyncio.to_thread(close_e2b_sandbox, sandbox)
            except Exception as exc:
                logger.warning("Failed to clean up E2B sandbox: %s", exc)
            raise
        context.code_env = sandbox
        context.code_env_owned = True

    def _upload_skills(self, sandbox: Any, skills: list[SkillInfo]) -> None:
        """Upload complete skill directories to the sandbox."""
        for skill in skills:
            skill_name = skill.name
            if (
                not skill_name
                or skill_name in {".", ".."}
                or "/" in skill_name
                or "\\" in skill_name
                or PurePosixPath(skill_name).name != skill_name
            ):
                raise ValueError(f"Invalid skill name: {skill_name!r}")

            skill_root = Path(skill.path).resolve()
            if not skill_root.is_dir():
                raise ValueError(
                    f"Skill path for {skill_name!r} is not a directory: {skill_root}"
                )

            remote_root = PurePosixPath("/home/user/skills") / skill_name
            for source_path in sorted(skill_root.rglob("*")):
                if source_path.is_symlink() or not source_path.is_file():
                    continue

                relative_path = source_path.relative_to(skill_root)
                remote_path = remote_root.joinpath(
                    *(part for part in relative_path.parts)
                )
                try:
                    payload = source_path.read_bytes()
                    sandbox.files.write(str(remote_path), payload)
                except Exception as exc:
                    raise RuntimeError(
                        f"Failed to upload skill {skill_name!r} file "
                        f"{source_path} to {remote_path}"
                    ) from exc

    def _register_sandbox_tools(self, sandbox) -> None:
        """Register sandbox-executable tools through the E2B adapter."""
        register_sandbox_tools(sandbox, self._sandbox_tools)

    def _get_sandbox_tools_prompt(self) -> str:
        """Generate prompt describign sandbox-executable tools"""
        if not self._sandbox_tools:
            return ""
        tool_definitions = [t.tool_definition for t in self._sandbox_tools]
        tools_json = json.dumps(tool_definitions, indent=2, ensure_ascii=False)
        return (
            "\n\n## Sandbox-Executable Tools\n"
            "The following functions are pre-registered in the sandbox "
            "and can be called directly in your Python code:\n"
            f"{tools_json}"
        )

    async def _process_confirmations(
        self,
        context: ExecutionContext,
        confirmations: list[ToolConfirmation],
    ) -> None:
        """Process tool confirmations from human-in-the-loop"""
        raw_pending = context.state.get("pending_tool_calls", [])
        pending = [PendingToolCall.model_validate(d) for d in raw_pending]

        tools_dict = {t.name: t for t in self.tools}
        results: list[ToolResult] = []
        remaining: list[PendingToolCall] = []
        supplied_ids = {c.tool_call_id for c in confirmations}

        for pending_call in pending:
            tc = pending_call.tool_call
            confirmation = next(
                (c for c in confirmations if c.tool_call_id == tc.tool_call_id),
                None,
            )

            if confirmation is None:
                remaining.append(pending_call)
                continue

            if confirmation.approved:
                args = confirmation.modified_arguments or tc.arguments
                if isinstance(args, str):
                    args = json.loads(args)

                tool_obj = tools_dict.get(tc.name)
                if tool_obj:
                    try:
                        output = await tool_obj(context, **args)
                        results.append(
                            ToolResult(
                                tool_call_id=tc.tool_call_id,
                                name=tc.name,
                                status="success",
                                content=[output],
                            )
                        )
                    except Exception as e:
                        results.append(
                            ToolResult(
                                tool_call_id=tc.tool_call_id,
                                name=tc.name,
                                status="error",
                                content=[str(e)],
                            )
                        )
            else:
                results.append(
                    ToolResult(
                        tool_call_id=tc.tool_call_id,
                        name=tc.name,
                        status="error",
                        content=["User denied the tool execution."],
                    )
                )

        if remaining:
            context.state["pending_tool_calls"] = [p.model_dump() for p in remaining]
        else:
            context.state.pop("pending_tool_calls", None)
            tool_event = Event(
                execution_id=context.execution_id,
                author=self.name,
                content=results,
            )
            context.add_event(tool_event)

    def _log_response(self, response: LlmResponse) -> None:
        """Log LLM response for verbose mode."""
        for item in response.content:
            if isinstance(item, Message):
                logger.info(f"[{self.name}] {item.content}")
            elif isinstance(item, ToolCall):
                logger.info(f"[{self.name}] Tool Call: {item.name}({item.arguments})")

    # handle multi-agents
    def _get_transfer_targets(self) -> list[Agent]:
        """List of targets the current agent can transfer to"""

        targets: list[Agent] = []

        # 1. Children
        targets.extend(self.sub_agents)

        # 2. Parent and siblings 兄弟姐妹
        if self.parent:
            targets.append(self.parent)

            # 3. Siblings (Optional)
            if not self.disallow_transfer_to_peers:
                for sibling in self.parent.sub_agents:
                    if sibling.name != self.name:
                        targets.append(sibling)

        return targets

    def _find_agent(self, name: str) -> Agent | None:
        """Search by name across the entire agent tree"""
        root = self
        while root.parent:
            root = root.parent
        return root._find_in_subtree(name)

    def _find_in_subtree(self, name: str) -> Agent | None:
        """Search in current agent and subtree 递归查找."""
        if self.name == name:
            return self
        for sub in self.sub_agents:
            if found := sub._find_in_subtree(name):
                return found
        return None

    def _validate_and_set_sub_agents(self) -> None:
        """Validate name/parent duplicates in sub_agents and set parent."""
        seen_names = set()
        for sub in self.sub_agents:
            if sub.name in seen_names:
                raise ValueError(f"Duplicate sub-agent name: '{sub.name}'")
            seen_names.add(sub.name)

            if sub.parent is not None:
                raise ValueError(
                    f"Agent '{sub.name}' already has parent '{sub.parent.name}'"
                )
            sub.parent = self
