"""skill-agent 示例：演示技能系统 + E2B 沙箱执行

原理
----
Agent 通过 ``skills_path`` 加载本地技能目录下的 SKILL.md 说明文档，
模型先读取技能说明，再按其中的工作流调用沙箱工具完成任务。本例的
pdf-merge 技能指导模型：上传 PDF → 安装 pypdf 依赖 → 用 pypdf 的
PdfReader/PdfWriter 合并 → 写回结果文件并校验页数。

沙箱是独立且默认禁网的 Linux 环境，依赖不随本地 venv 共享，因此
工作流显式用 base_e2b_tool 执行 ``pip install pypdf`` 装依赖；沙箱
联网能力与 shell 命令超时分别由 src 的 create_e2b_sandbox
(allow_internet_access) 与 base_e2b_tool (timeout) 提供。

关键 API
--------
  Agent(..., code_execution="e2b", skills_path=...)
  await agent.prepare_code_env(context, caller_owns_sandbox=True)
  tools: upload_file_to_e2b / execute_python_in_e2b / base_e2b_tool

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  uv run python examples/skill_agent.py

前置条件
--------
  - E2B_API_KEY 已配置（.env）；
  - ``D:\\pdf_files`` 下恰好有 3 个 PDF（不含 merged.pdf）。
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

if __package__ is None or __package__ == "":
    package_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(package_dir.parent))
    sys.path.insert(0, str(package_dir))

from scratchagent import Agent
from scratchagent import ExecutionContext, ToolResult
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.sandbox import close_e2b_sandbox

INPUT_DIR = Path(r"D:\pdf_files")
OUTPUT_NAME = "merged.pdf"
SANDBOX_OUTPUT = "/home/user/merged.pdf"
SANDBOX_INPUT_DIR = "/home/user/pdf_inputs"
EXPECTED_INPUT_COUNT = 3


def select_pdf_files(input_dir: Path = INPUT_DIR) -> list[Path]:
    """Return the three direct PDF inputs in deterministic filename order."""
    output_name = OUTPUT_NAME.casefold()
    pdf_files = [
        path
        for path in input_dir.iterdir()
        if path.is_file()
        and path.suffix.casefold() == ".pdf"
        and path.name.casefold() != output_name
    ]
    pdf_files.sort(key=lambda path: (path.name.casefold(), path.name))
    if len(pdf_files) != EXPECTED_INPUT_COUNT:
        names = ", ".join(path.name for path in pdf_files) or "none"
        raise ValueError(
            f"Expected exactly {EXPECTED_INPUT_COUNT} input PDFs in {input_dir}, "
            f"found {len(pdf_files)}: {names}"
        )
    if any(path.stat().st_size == 0 for path in pdf_files):
        raise ValueError("PDF inputs must not be empty.")
    return pdf_files


def sandbox_path_for(source_path: Path) -> str:
    """Return the fixed E2B upload path for one local source file."""
    return f"{SANDBOX_INPUT_DIR}/{source_path.name}"


def _tool_results(context: ExecutionContext) -> list[ToolResult]:
    return [
        item
        for event in context.events
        for item in event.content
        if isinstance(item, ToolResult)
    ]


def verify_agent_workflow(context: ExecutionContext, source_files: list[Path]) -> None:
    """Ensure the agent completed every required E2B action successfully."""
    tool_results = _tool_results(context)
    failed = [item for item in tool_results if item.status != "success"]
    if failed:
        failure_details = "\n".join(str(item.content) for item in failed)
        if "No module named 'pypdf'" in failure_details:
            raise RuntimeError(
                "The E2B image does not include pypdf, so the pdf-merge skill "
                "cannot run. Use an E2B template with pypdf installed."
            )
        raise RuntimeError(f"A sandbox tool call failed: {failed}")

    uploads = [item for item in tool_results if item.name == "upload_file_to_e2b"]
    if len(uploads) != len(source_files):
        raise RuntimeError(
            f"Expected {len(source_files)} upload_file_to_e2b calls, found {len(uploads)}."
        )
    if not any(item.name == "execute_python_in_e2b" for item in tool_results):
        raise RuntimeError(
            "The agent did not run the PDF merge in execute_python_in_e2b."
        )


def validate_merged_pdf(
    merged_bytes: bytes,
    source_files: list[Path],
) -> None:
    """Check the downloaded PDF is readable and contains all source pages."""
    if not merged_bytes.startswith(b"%PDF-"):
        raise ValueError("The sandbox output is not a PDF file.")

    import fitz

    source_page_count = 0
    for source_path in source_files:
        with fitz.open(source_path) as source_document:
            source_page_count += source_document.page_count

    with fitz.open(stream=merged_bytes, filetype="pdf") as merged_document:
        if merged_document.page_count != source_page_count:
            raise ValueError(
                "Merged PDF page count does not match its source PDFs: "
                f"expected {source_page_count}, got {merged_document.page_count}."
            )


def write_merged_pdf(output_path: Path, merged_bytes: bytes) -> None:
    """Replace the output only after the complete artifact is written."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="wb", suffix=".pdf", prefix="merged-", dir=output_path.parent, delete=False
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
        temporary_file.write(merged_bytes)
    try:
        temporary_path.replace(output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def build_prompt(source_files: list[Path]) -> str:
    uploads = "\n".join(
        f"- Local path: {source_path}\n  Sandbox path: {sandbox_path_for(source_path)}"
        for source_path in source_files
    )
    sandbox_files = ", ".join(
        repr(sandbox_path_for(source_path)) for source_path in source_files
    )
    return f"""Merge exactly these PDFs in the listed order.

{uploads}

You must follow this workflow exactly:
1. Read /home/user/skills/pdf-merge/SKILL.md before doing any PDF work.
2. Use upload_file_to_e2b once for each listed local path and its exact sandbox path.
3. Install the pypdf dependency in the sandbox first: use base_e2b_tool to run the shell
   command `pip install pypdf`. Do not skip this step and do not substitute another PDF
   library.
4. Use execute_python_in_e2b to check that pypdf can be imported. If it cannot, report
   the error.
5. Use execute_python_in_e2b and the pypdf PdfReader/PdfWriter pattern from the skill to
   merge these sandbox files in this exact order: [{sandbox_files}].
6. Write only the resulting PDF to {SANDBOX_OUTPUT}, then use Python to report its page
   count and byte size. Do not claim success unless that file was created.
"""


async def read_sandbox_bytes(sandbox: Any, sandbox_path: str) -> bytes:
    payload = await asyncio.to_thread(sandbox.files.read, sandbox_path, format="bytes")
    merged_bytes = bytes(payload)
    if not merged_bytes:
        raise ValueError("The sandbox produced an empty output file.")
    return merged_bytes


async def skill_agent_test() -> None:
    """Merge the configured local PDFs through the E2B-backed pdf-merge skill."""
    source_files = select_pdf_files()
    output_path = INPUT_DIR / OUTPUT_NAME
    skills_path = Path(__file__).resolve().parent / "skills"

    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT,
            model="gpt-5.5",
        )
    )
    skill_agent = Agent(
        model=openai_client,
        tools=[],
        max_steps=10,
        instruction=(
            "You have access to a sandboxed Linux environment and the upload_file and "
            "execute_python tools. Follow the supplied PDF workflow precisely."
        ),
        code_execution="e2b",
        skills_path=str(skills_path),
    )
    context = ExecutionContext()
    await skill_agent.prepare_code_env(context, caller_owns_sandbox=True)
    try:
        result = await skill_agent.run(build_prompt(source_files), context=context, verbose=True)
        verify_agent_workflow(result.context, source_files)
        merged_bytes = await read_sandbox_bytes(context.code_env, SANDBOX_OUTPUT)
        validate_merged_pdf(merged_bytes, source_files)
        write_merged_pdf(output_path, merged_bytes)
    finally:
        if context.code_env is not None:
            await asyncio.to_thread(close_e2b_sandbox, context.code_env)
            context.code_env = None
            context.code_env_owned = False

    print(f"Merged {len(source_files)} PDFs into {output_path}")
    print(f"Agent response: {result.output}")


if __name__ == "__main__":
    asyncio.run(skill_agent_test())
