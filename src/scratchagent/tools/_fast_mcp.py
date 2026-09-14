"""本地MCP 服务用的 mcp 工具"""

import json
from contextlib import asynccontextmanager

from fastmcp import Client

from ._base import BaseTool, FunctionTool
from ._helpers import format_tool_definition

# 提供一个本地MCP 服务地址
DEFAULT_MCP_SERVER_URL = "http://127.0.0.1:8800/mcp"

def _json_text(value) -> str:
    """将结构化 MCP 结果转换为适用于大语言模型工具消息的文本."""
    if isinstance(value, str):
        return value

    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)

def _extract_result_content(result) -> str:
    """从 FastMCP CallToolResult 中提取稳定文本值."""
    data = getattr(result, "data", None)
    if data is not None:
        return _json_text(data)

    parts = []
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text is not None:
            parts.append(text)

    if parts:
        return "\n".join(parts)

    structured_content = getattr(result, "structured_content", None)
    if structured_content is not None:
        return _json_text(structured_content)

    return ""

def _get_tools(mcp_tools):
    """支持 FastMCP 列表以及 MCP ListToolsResult."""
    if isinstance(mcp_tools, list):
        return mcp_tools
    return mcp_tools.tools

def _create_mcp_tool(
    mcp_tool,
    server_url: str = DEFAULT_MCP_SERVER_URL,
) -> FunctionTool:
    """创建一个封装 FastMCP HTTP 工具的 FunctionTool."""

    async def call_mcp(**kwargs):
        async with Client(server_url) as client:
            result = await client.call_tool(mcp_tool.name, kwargs)
            return _extract_result_content(result)

    tool_definition = format_tool_definition(
        name=mcp_tool.name,
        description=mcp_tool.description or "",
        parameters=mcp_tool.input_schema
    )

    return FunctionTool(
        func=call_mcp,
        name=mcp_tool.name,
        description=mcp_tool.description or "",
        tool_definition=tool_definition,
    )

async def load_mcp_tools(
    server_url: str = DEFAULT_MCP_SERVER_URL,
) -> list[BaseTool]:
    """从 FastMCP HTTP 服务器加载工具作为函数工具.

    每次调用返回的工具都会新建一条 HTTP 连接.
    """
    async with Client(server_url) as client:
        mcp_tools = await client.list_tools()

    return [_create_mcp_tool(tool, server_url) for tool in _get_tools(mcp_tools)]


# @asynccontextmanager
# async def mcp_connection(server_url: str = DEFAULT_MCP_SERVER_URL):
#     """保持与 FastMCP 流式 HTTP 服务器的连接.

#     Usage:
#         async with mcp_connection() as client:
#             tools = await client.list_tools()
#             result = await client.call_tool("tool_name", {"argument": "value"})
#     """
#     async with Client(server_url) as client:
#         yield client
