"""检索增强生成 RAG 功能：嵌入、分块与向量搜索"""

import os
from typing import TypedDict

import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

from .config import load_project_env


class SearchResult(TypedDict):
    """向量收索结果： 一个文本块及其与查询的相似度"""

    chunk: str
    similarity: float


def get_embeddings(
    texts: str | list[str], model: str | None = None
) -> np.ndarray:
    """
    使用 OpenAI 的嵌入模型获取一组文本的嵌入向量.

    Args:
        texts : 待嵌入的文本列表.
        model : 嵌入模型. 若为 None 则读取环境变量 EMBEDDING_MODEL.

    Returns:
        每个文本对应的向量列表.
    """
    # 这里开启是否加载环境变量
    load_project_env()
    # 这里使用 OpenRouter 的 API Key 和 Base URL 来创建 OpenAI 客户端
    # 因为 "text-embedding-3-small", 中转平台没有提供
    if model is None:
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL"),
        timeout=120.0,          # 放宽客户端总超时
        max_retries=2,          # 失败自动重试，抵御网络抖动    
    )
    if isinstance(texts, str):
        texts = [texts]

    response = client.embeddings.create(model=model, input=texts)
    embeddings = np.array([item.embedding for item in response.data])
    return embeddings


def fixed_length_chunking(
    text: str, chunk_size: int = 200, overlap: int = 50
) -> list[str]:
    """
    将文本切分为固定长度的文本块，可选择设置重叠部分.

    Args:
        text : 要拆分的文字
        chunk_size : 每个块的大小.
        overlap : 两个块之间的字符重叠数.

    Returns:
        文本块列表.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def vector_search(
    query: str, chunks: list[str], chunk_embeddings: np.ndarray, top_k: int = 3
) -> list[SearchResult]:
    """
    执行向量搜索，为给定查询找出最相关的文本块.

    Args:
        query : 查询文本.
        chunks : 文本块列表.
        chunk_embeddings: 预备计算的嵌入模型向量列表.
        top_k : 返回Top 数.

    Returns:
        最相关的块列表.
    """
    query_embedding = get_embeddings(query)
    similarities = cosine_similarity(query_embedding, chunk_embeddings)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]

    results: list[SearchResult] = []
    for idx in top_indices:
        results.append(
            {
                "chunk": chunks[idx],
                "similarity": similarities[idx],
            }
        )

    return results
