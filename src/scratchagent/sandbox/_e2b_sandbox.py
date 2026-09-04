"""E2B 代码解释器沙箱集成"""

import os
from pathlib import Path
from typing import Any, Iterable
from dotenv import load_dotenv

DEFAULT_TIMEOUT_SECONDS = 300


class E2BSandboxConfigurationError(RuntimeError):
    """当 E2B 沙箱无法完成配置时抛出."""


def _load_project_environment() -> None:
    """在不覆盖进程变量的前提下加载仓库环境."""
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(project_root / ".env", override=False)


def create_e2b_sandbox(
    *,
    api_key: str | None = None,
    template: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    allow_internet_access: bool = False,
) -> Any:
    """创建一个E2B 执行沙箱环境.

    ``timeout`` is measured in seconds by the E2B SDK. Network access is
    disabled by default and must be explicitly enabled by the caller. Set
    ``E2B_TEMPLATE_ID`` (or ``E2B_TEMPLATE``) to use a custom E2B template.
    """
    _load_project_environment()
    resolved_key = api_key or os.getenv("E2B_API_KEY")
    template = template or os.getenv("E2B_TEMPLATE_ID") or os.getenv("E2B_TEMPLATE")
    if not resolved_key:
        raise E2BSandboxConfigurationError(
            "E2B_API_KEY is not configured; set it in the environment or .env."
        )
    if timeout <= 0:
        raise ValueError("E2B sandbox timeout must be positive seconds.")

    try:
        from e2b_code_interpreter import Sandbox

        create_options: dict[str, Any] = {
            "api_key": resolved_key,
            "timeout": timeout,
            "allow_internet_access": allow_internet_access,
        }
        if template:
            create_options["template"] = template
        return Sandbox.create(**create_options)
    except E2BSandboxConfigurationError:
        raise
    except Exception as exc:
        raise E2BSandboxConfigurationError("Failed to create the E2B sandbox.") from exc


def register_sandbox_tools(sandbox: Any, tools: Iterable[Any]) -> None:
    """在沙箱中注册便携沙箱可执行工具函数 in ``sandbox``."""
    sources = [tool.get_source_code() for tool in tools]
    if not sources:
        return

    execution = sandbox.run_code("\n\n".join(sources))
    error = getattr(execution, "error", None)
    if error:
        raise RuntimeError(f"Failed to register sandbox tools: {error}")


def close_e2b_sandbox(sandbox: Any) -> None:
    """终止 E2B 沙箱，允许调用方记录清理失败信息."""
    if sandbox is not None:
        sandbox.kill()
