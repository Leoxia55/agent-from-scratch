"""tools/_code_execution.py 单元测试：E2B 代码执行工具。"""

from __future__ import annotations

import pytest

from scratchagent import ExecutionContext
from scratchagent.tools import (
    base_e2b_tool,
    execute_python_in_e2b,
    upload_file_to_e2b,
)
from scratchagent.tools._code_execution import _execution_output


class FakeExecution:
    def __init__(self, error=None, to_json_result="{}"):
        self.error = error
        self._json = to_json_result

    def to_json(self):
        return self._json


class TestExecutionOutput:
    def test_error_raises(self):
        exec_ = FakeExecution(error="boom")
        with pytest.raises(RuntimeError, match="boom"):
            _execution_output(exec_)

    def test_str_result(self):
        exec_ = FakeExecution(to_json_result="result")
        assert _execution_output(exec_) == "result"

    def test_dict_result(self):
        exec_ = FakeExecution(to_json_result={"a": 1})
        out = _execution_output(exec_)
        assert "a" in out


class TestExecutePythonInE2b:
    async def test_no_code_env(self):
        ctx = ExecutionContext()
        with pytest.raises(RuntimeError, match="No code execution environment"):
            await execute_python_in_e2b(ctx, code="print(1)")

    async def test_with_code_env(self, monkeypatch):
        import asyncio

        ctx = ExecutionContext()
        ctx.code_env = type(
            "Env",
            (),
            {"run_code": lambda self, code: FakeExecution(to_json_result="ok")},
        )()
        # 绕过 asyncio.to_thread 的真实线程
        result = await execute_python_in_e2b(ctx, code="print(1)")
        assert result == "ok"


class TestBaseE2bTool:
    async def test_no_code_env(self):
        ctx = ExecutionContext()
        with pytest.raises(RuntimeError, match="No code execution environment"):
            await base_e2b_tool(ctx, command="ls")

    async def test_stdout_stderr(self):
        ctx = ExecutionContext()
        result = type("R", (), {"stdout": "out", "stderr": "err"})()
        ctx.code_env = type(
            "Env", (), {"commands": type("C", (), {"run": lambda s, c: result})()}
        )()
        out = await base_e2b_tool(ctx, command="ls")
        assert "out" in out
        assert "err" in out

    async def test_no_output(self):
        ctx = ExecutionContext()
        result = type("R", (), {"stdout": "", "stderr": ""})()
        ctx.code_env = type(
            "Env", (), {"commands": type("C", (), {"run": lambda s, c: result})()}
        )()
        out = await base_e2b_tool(ctx, command="ls")
        assert "no output" in out


class TestUploadFileToE2b:
    async def test_no_code_env(self, tmp_path):
        ctx = ExecutionContext()
        f = tmp_path / "x.txt"
        f.write_text("data")
        with pytest.raises(RuntimeError, match="No code execution environment"):
            await upload_file_to_e2b(ctx, local_path=str(f))

    async def test_default_path(self, tmp_path):
        ctx = ExecutionContext()
        f = tmp_path / "x.txt"
        f.write_text("data")
        written = {}

        class FakeFiles:
            def write(self, path, payload):
                written["path"] = path
                written["payload"] = payload

        ctx.code_env = type("Env", (), {"files": FakeFiles()})()
        out = await upload_file_to_e2b(ctx, local_path=str(f))
        assert "/home/user/x.txt" in written["path"]
        assert written["payload"] == b"data"
        assert "x.txt" in out
