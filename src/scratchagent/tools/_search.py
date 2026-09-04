"""一个使用 Tavily 的web 查询工具"""

import os
from typing import Optional, List, Dict
from tavily import TavilyClient

def search_web(
        query: str,
        max_results: int = 5,
        topic: str = "general",
        time_range: str | None = None,
) -> List[Dict]:
    """使用 Tavily API 进行web 查询.

    Args:
        query: Search query string
        max_results: Maximum number of results to return 
        topic: Search topic - 'general' or 'news'
        time_range: Time range filter(e.g., 'day', 'week', 'month', 'year')
    """

    client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
    kwargs = {
        "query" : query,
        "max_results": max_results,
        "topic": topic,
    }
    if time_range:
        kwargs["time_range"] = time_range

    response = client.search(**kwargs)
    return response.get("results", [])

