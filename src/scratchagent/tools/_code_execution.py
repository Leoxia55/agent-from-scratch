"""使用 E2B 沙箱的代码执行工具"""

import asyncio
import json
import os
from typing import Any

from ..context import ExecutionContext
from ._base import tool


def _execution_output(execution: Any) -> str:
    """以可读格式返回软件开发工具包（SDK）的执行结果，禁止二次编码生成 JSON 数据."""
    error = getattr(execution, "error", None)
    if error:
        raise RuntimeError(f"Python execution failed: {error}")

    serialized = execution.to_json()
    if isinstance(serialized, str):
        return serialized
    return json.dumps(serialized, indent=2, ensure_ascii=False)


@tool(  # type: ignore[reportArgumentType]
    name="execute_python_in_e2b",
    description=(
        "Execute Python code in an isolated E2B sandbox. "
        "Use this for calculations, data processing, or Python operations."
    ),
)
async def execute_python_in_e2b(context: ExecutionContext, code: str) -> str:
    """在 E2B 沙箱中执行 Python 代码."""
    if context.code_env is None:
        raise RuntimeError("No code execution environment available.")
    execution = await asyncio.to_thread(context.code_env.run_code, code)
    return _execution_output(execution)


@tool(  # type: ignore[reportArgumentType]
    name="base_e2b_tool", description="Execute a shell command in an E2B sandbox."
)
async def base_e2b_tool(context: ExecutionContext, command: str) -> str:
    """在 E2B 沙箱中执行 shell 命令."""
    if context.code_env is None:
        raise RuntimeError("No code execution environment available.")

    result = await asyncio.to_thread(context.code_env.commands.run, command)
    output_parts = []
    if getattr(result, "stdout", None):
        output_parts.append(result.stdout)
    if getattr(result, "stderr", None):
        output_parts.append(f"STDERR: {result.stderr}")
    return "\n".join(output_parts) if output_parts else "Command completed (no output)"


@tool(  # type: ignore[reportArgumentType]
    name="upload_file_to_e2b", description="Upload a local file to an E2B sandbox."
)
async def upload_file_to_e2b(
    context: ExecutionContext,
    local_path: str,
    sandbox_path: str | None = None,
) -> str:
    """上传本地文件到 E2B 沙箱."""
    if context.code_env is None:
        raise RuntimeError("No code execution environment available.")

    if sandbox_path is None:
        sandbox_path = f"/home/user/{os.path.basename(local_path)}"

    with open(local_path, "rb") as file_handle:
        payload = file_handle.read()
    await asyncio.to_thread(context.code_env.files.write, sandbox_path, payload)
    return f"File uploaded to {sandbox_path}"
