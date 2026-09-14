"""回调函数工具, 用于Agent 审批和压缩"""

import json
from collections.abc import Mapping

from ..context import ExecutionContext
from ..rag import fixed_length_chunking, get_embeddings, vector_search
from ..types import ToolCall, ToolResult

DANGEROUS_TOOLS = ["delete_file", "send_email", "execute_sql"]


def approval_callback(context: ExecutionContext, tool_call: ToolCall):
    """执行危险工具前请求用户批准."""
    if tool_call.name not in DANGEROUS_TOOLS:
        return None
    print("\n⚠️ Dangerous tool execution requested")
    print(f"Tool: {tool_call.name}")
    print(f"Arguments: {tool_call.arguments}")

    response = (
        input("Do you approve the execution of this tool? (y/n): ").strip().lower()
    )
    if response == "y":
        print("✅ Approved. Executing...\n")
        return None
    print("❌ Rejected. Tool execution will not proceed.\n")
    return f"User denied execution of the tool '{tool_call.name}'."


def _extract_search_query(context: ExecutionContext, tool_call_id: str) -> str:
    """从上下文中提取原始搜索查询."""
    for event in context.events:
        for item in event.content:
            if not isinstance(item, ToolCall) or item.tool_call_id != tool_call_id:
                continue
            arguments = item.arguments
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    return ""
            if isinstance(arguments, Mapping):
                query = arguments.get("query", "")
                return query if isinstance(query, str) else ""
    return ""


def search_compressor(context: ExecutionContext, tool_result: ToolResult):
    """基于查询的向量检索压缩搜索结果."""
    if tool_result.name not in {"search_web", "search_documents"}:
        return None
    if tool_result.status != "success" or not tool_result.content:
        return None

    original_content = tool_result.content[0]
    query = _extract_search_query(context, tool_result.tool_call_id)
    if not query:
        return None

    if tool_result.name == "search_documents":
        if not isinstance(original_content, list) or not all(
            isinstance(document, str) for document in original_content
        ):
            return None
        chunks: list[str] = original_content
    else:
        if isinstance(original_content, list):
            web_items = [item for item in original_content if isinstance(item, Mapping)]
            web_text = "\n\n".join(
                "\n".join(
                    str(value)
                    for key in ("title", "content", "url")
                    if (value := item.get(key))
                )
                for item in web_items
            )
        elif isinstance(original_content, str):
            web_text = original_content
        else:
            return None
        if len(web_text) < 2000:
            return None
        chunks = fixed_length_chunking(web_text, chunk_size=500, overlap=50)

    if not chunks:
        return None
    embeddings = get_embeddings(chunks)
    results = vector_search(query, chunks, embeddings, top_k=3)
    compressed: list[str] = [result["chunk"] for result in results]
    result_content: list[str | list[str] | list[dict]]
    if tool_result.name == "search_documents":
        result_content = [*compressed]
    else:
        result_content = ["\n\n".join(compressed)]

    return ToolResult(
        tool_call_id=tool_result.tool_call_id,
        name=tool_result.name,
        status="success",
        content=result_content,
    )
