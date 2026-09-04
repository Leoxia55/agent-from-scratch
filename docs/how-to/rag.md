# 接入 RAG

内置 RAG 是轻量的“切块 + embedding + 余弦相似度”流程，适合教学和小规模实验。

## 1. 切块与向量化

```python
from scratchagent import fixed_length_chunking, get_embeddings, vector_search

text = open("notes.md", encoding="utf-8").read()
chunks = fixed_length_chunking(text, chunk_size=500, overlap=80)
embeddings = get_embeddings(chunks)
hits = vector_search("如何配置超时？", chunks, embeddings, top_k=3)
```

`fixed_length_chunking` 使用字符偏移，不理解 Markdown 或句子边界；必须保持 `0 <= overlap < chunk_size`。`vector_search` 返回按相似度排序的字典：`{"chunk": ..., "similarity": ...}`。

## 2. 注入 Agent

```python
from scratchagent.tools import tool


@tool(description="搜索项目文档")
def search_docs(query: str) -> list[dict]:
    return vector_search(query, chunks, embeddings, top_k=3)


agent = Agent(
    model=client,
    instruction="回答前先搜索项目文档；无法找到依据时明确说明。",
    tools=[search_docs],
)
```

embedding 客户端读取 `OPENROUTER_API_KEY` 和 `OPENROUTER_BASE_URL`。生产环境应持久化向量库、过滤租户、限制返回片段，并把检索内容视为不可信上下文。

