"""一个通过 FastMCP 构建的 MCP 服务器"""

from fastmcp import FastMCP

mcp = FastMCP("通过FastMCP 构建的远程MCP")

@mcp.tool
def greet(name: str) -> str:
    """一个简单的工具示例：问候 + user"""
    return f"你好，{name}!"

@mcp.tool
def count_words(text: str) -> int:
    """一个简单的工具：用于统计给出的文本有多少个词 word"""
    return len(text.split())

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8800)
