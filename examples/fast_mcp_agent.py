"""Agent + FastMCP 本地服务端到端测试。"""

import asyncio
import socket
import subprocess
import sys
from pathlib import Path

from scratchagent import Agent
from scratchagent.llm import(
    LlmClient,
    Provider,
    resolve_model_config
)
from scratchagent.tools import load_mcp_tools

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8800
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/mcp"
# 注意 文件所在的路径
SERVER_FILE = Path(__file__).resolve().parents[0] /"remote_server_fast_demo.py"

async def wait_for_server(timeout: float = 10.0) -> None:
    """等待 FastMCP HTTP 服务开始监听..."""
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        try:
            with socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=0.5):
                return
        except OSError:
            await asyncio.sleep(0.2)
    raise TimeoutError(f"MCP 服务未在 {timeout:.1f} 秒内启动：{SERVER_URL}")

def start_mcp_server() -> subprocess.Popen:
    """启动本地 FastMCP 服务器， 并返回子进程句柄"""
    return subprocess.Popen (
        [sys.executable, str(SERVER_FILE)],
        cwd=str(SERVER_FILE.parent.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,        
    )

def stop_mcp_server(process: subprocess.Popen) -> None:
    """停止本测试启动的 MCP 服务。"""
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

async def run_agent_test() -> None:
    """加载两个 MCP 工具，并让 Agent 实际调用它们。"""
    mcp_tools = await load_mcp_tools(SERVER_URL)
    tool_names = {tool.name for tool in mcp_tools}
    expected_names = {"greet", "count_words"}
    assert tool_names == expected_names, f"MCP 工具不匹配: {tool_names}"

    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT,
            model="gpt-5.5",
        )
    )

    agent = Agent(
        model=openai_client,
        tools=mcp_tools,
        instruction=(
            "You are testing two MCP tools. For every request, call both tools "
            "before answering. Report the exact tool results clearly."
        ),
        max_steps=5,
    )
    result = await agent.run(
        "请调用 greet，name 使用 'Persist'；同时调用 count_words，"
        "text 使用 'You are testing two MCP tools. For every request, call both tools "
            "before answering. Report the exact tool results clearly'。最后汇总两个工具的原始结果。"
    )

    output = str(result.output)
    print(f"Agent 输出：{output}")

async def main() -> None:
    process = start_mcp_server()
    try:
        await wait_for_server()
        await run_agent_test()
    finally:
        stop_mcp_server(process)

if __name__ == "__main__":
    asyncio.run(main())  