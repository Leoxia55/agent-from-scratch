"""sandbox/_e2b_sandbox.py 单元测试：E2B 沙箱生命周期。"""

from __future__ import annotations

import pytest

from scratchagent.sandbox import (
    close_e2b_sandbox,
    create_e2b_sandbox,
    register_sandbox_tools,
)
from scratchagent.sandbox._e2b_sandbox import E2BSandboxConfigurationError


class TestCreateE2bSandbox:
    def test_missing_key(self, monkeypatch):
        monkeypatch.delenv("E2B_API_KEY", raising=False)
        with pytest.raises(E2BSandboxConfigurationError):
            create_e2b_sandbox()

    def test_timeout_nonpositive(self, monkeypatch):
        monkeypatch.setenv("E2B_API_KEY", "key")
        with pytest.raises(ValueError):
            create_e2b_sandbox(timeout=0)

    def test_returns_sandbox(self, monkeypatch):
        monkeypatch.setenv("E2B_API_KEY", "key")
        captured = {}

        class FakeSandbox:
            @classmethod
            def create(cls, **kwargs):
                captured.update(kwargs)
                return "sandbox"

        # create_e2b_sandbox 内部 `from e2b_code_interpreter import Sandbox`，
        # 通过替换 sys.modules 注入 fake
        import sys
        import types

        fake_e2b = types.ModuleType("e2b_code_interpreter")
        fake_e2b.Sandbox = FakeSandbox
        monkeypatch.setitem(sys.modules, "e2b_code_interpreter", fake_e2b)

        result = create_e2b_sandbox(timeout=120, allow_internet_access=True)
        assert result == "sandbox"
        assert captured["timeout"] == 120
        assert captured["allow_internet_access"] is True

    def test_template_from_env(self, monkeypatch):
        monkeypatch.setenv("E2B_API_KEY", "key")
        monkeypatch.setenv("E2B_TEMPLATE_ID", "custom-template")
        captured = {}

        class FakeSandbox:
            @classmethod
            def create(cls, **kwargs):
                captured.update(kwargs)
                return "sandbox"

        import sys
        import types

        fake_e2b = types.ModuleType("e2b_code_interpreter")
        fake_e2b.Sandbox = FakeSandbox
        monkeypatch.setitem(sys.modules, "e2b_code_interpreter", fake_e2b)

        create_e2b_sandbox()
        assert captured["template"] == "custom-template"


class TestRegisterSandboxTools:
    def test_empty_tools(self):
        sandbox = object()
        register_sandbox_tools(sandbox, [])  # 不抛错

    def test_error_raises(self):
        class FakeExec:
            error = "boom"

        sandbox = type("S", (), {"run_code": lambda self, code: FakeExec()})()

        class FakeTool:
            def get_source_code(self):
                return "def f(): pass"

        with pytest.raises(RuntimeError, match="boom"):
            register_sandbox_tools(sandbox, [FakeTool()])


class TestCloseSandbox:
    def test_close_calls_kill(self):
        sandbox = type("S", (), {"kill": lambda self: setattr(self, "killed", True)})()
        close_e2b_sandbox(sandbox)
        assert sandbox.killed is True

    def test_close_none(self):
        close_e2b_sandbox(None)  # 不抛错
