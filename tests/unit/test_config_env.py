"""config.py 单元测试：统一环境 .env 加载。"""

from __future__ import annotations

from scratchagent import config
from scratchagent.config import load_project_env


def test_load_project_env_found_sets_flag(monkeypatch, tmp_path):
    """找到 .env 文件时，加载后置 _ENV_LOADED=True。"""
    monkeypatch.setattr(config, "_ENV_LOADED", False)
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n", encoding="utf-8")
    monkeypatch.setattr(config, "find_dotenv", lambda usecwd=True: str(env_file))
    load_project_env()
    assert config._ENV_LOADED is True


def test_load_project_env_no_dotenv(monkeypatch):
    """无 .env 文件时不抛错，且标志保持 False（下次仍会尝试）。"""
    monkeypatch.setattr(config, "_ENV_LOADED", False)
    monkeypatch.setattr(config, "find_dotenv", lambda usecwd=True: "")
    load_project_env()
    assert config._ENV_LOADED is False


def test_load_project_env_override_false(monkeypatch, tmp_path):
    """已存在的环境变量不应被 .env 覆盖（override=False）。"""
    monkeypatch.setattr(config, "_ENV_LOADED", False)
    monkeypatch.setenv("MY_TEST_VAR", "from_env")
    env_file = tmp_path / ".env"
    env_file.write_text("MY_TEST_VAR=from_dotenv\n", encoding="utf-8")
    monkeypatch.setattr(config, "find_dotenv", lambda usecwd=True: str(env_file))
    load_project_env()
    import os

    assert os.environ["MY_TEST_VAR"] == "from_env"


def test_load_project_env_second_call_noop(monkeypatch, tmp_path):
    """第二次调用直接 return，不重复加载。"""
    monkeypatch.setattr(config, "_ENV_LOADED", True)
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n", encoding="utf-8")
    # 标志已 True，find_dotenv 不应被调用
    calls = []
    monkeypatch.setattr(config, "find_dotenv", lambda usecwd=True: calls.append(1) or str(env_file))
    load_project_env()
    assert calls == []
