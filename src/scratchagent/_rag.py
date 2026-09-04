""" 检索增强生成 RAG 功能：嵌入、分块与向量搜索"""

import os
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import find_dotenv, load_dotenv

# 演示： import 的副作用，说明：项目入口加载过后 环境变量就有了
# 方法1： 直接注释
# load_dotenv(find_dotenv())

#方法2: 惰性加载，由于这个是一个可以独立的 RAG 服务，所以支持加载 .env

def load_project_env() -> None:
    """加载最近的.env 文件，且不暴露或覆盖已有变量值。

    已存在的进程环境变量优先级高于.env 文件内的变量。
    此举可保证测试、持续集成以及手动导出的 Shell 变量结果可复现。
    """
    env_file = find_dotenv(usecwd=True)
    if env_file:
        load_dotenv(env_file, override=False)


def get_embeddings(texts, model="text-embedding-3-small") -> np.ndarray:
    """
    使用 OpenAI 的嵌入模型获取一组文本的嵌入向量.

    Args:
        texts (list of str): List of texts to embed.
        model (str): The embedding model to use.

    Returns:
        np.ndarray: Array of embeddings.
    """
    # 这里开启是否加载环境变量
    load_project_env()
    # 这里使用 OpenRouter 的 API Key 和 Base URL 来创建 OpenAI 客户端
    # 因为 "text-embedding-3-small", 中转平台没有提供
    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL")
    )
    if isinstance(texts, str):
        texts = [texts]
    
    response = client.embeddings.create(
        model=model,
        input=texts
    )
    embeddings = np.array([item.embedding for item in response.data])
    return embeddings

def fixed_length_chunking(text, chunk_size=200, overlap=50) -> list[str]:
    """
    将文本切分为固定长度的文本块，可选择设置重叠部分.

    Args:
        text (str): The text to split.
        chunk_size (int): The size of each chunk.
        overlap (int): The number of overlapping characters between chunks.

    Returns:
        list of str: List of text chunks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def vector_search(query, chunks, chunk_embeddings, top_k=3) -> list:
    """
    执行向量搜索，为给定查询找出最相关的文本块.

    Args:
        query (str): The query text.
        chunks (list of str): List of text chunks.
        chunk_embeddings (np.ndarray): Precomputed embeddings for the chunks.
        top_k (int): Number of top results to return.

    Returns:
        list of str: List of the most relevant chunks.
    """
    query_embedding = get_embeddings(query)
    similarities = cosine_similarity(query_embedding, chunk_embeddings)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]

    results = []
    for idx in top_indices:
        results.append({
            'chunk': chunks[idx],
            'similarity': similarities[idx],
        })

    return results
