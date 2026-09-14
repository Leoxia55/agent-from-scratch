"""统一的环境.env加载, 全局只加载一次"""

from dotenv import find_dotenv, load_dotenv

_ENV_LOADED = False


def load_project_env() -> None:
    """加载最近的.env 文件，且不暴露或覆盖已有变量值。"""
    global _ENV_LOADED

    if _ENV_LOADED:
        return
    env_file = find_dotenv(usecwd=True)
    if env_file:
        load_dotenv(env_file, override=False)
        _ENV_LOADED = True
