"""rag.py 单元测试：分块、嵌入与向量搜索。"""

from __future__ import annotations

import numpy as np

from scratchagent.rag import fixed_length_chunking, vector_search


# ---------------------------------------------------------------- fixed_length_chunking
class TestFixedLengthChunking:
    def test_short_text(self):
        chunks = fixed_length_chunking("hello", chunk_size=10, overlap=0)
        assert chunks == ["hello"]

    def test_exact_boundary(self):
        text = "a" * 10
        chunks = fixed_length_chunking(text, chunk_size=5, overlap=0)
        assert chunks == ["aaaaa", "aaaaa"]

    def test_overlap(self):
        text = "abcdefghij"
        chunks = fixed_length_chunking(text, chunk_size=5, overlap=2)
        # start=0 -> abcde; start=3 -> defgh; start=6 -> ghij; start=9 -> j
        assert chunks == ["abcde", "defgh", "ghij", "j"]

    def test_no_overlap(self):
        text = "abcdefgh"
        chunks = fixed_length_chunking(text, chunk_size=3, overlap=0)
        assert chunks == ["abc", "def", "gh"]

    def test_empty_text(self):
        assert fixed_length_chunking("", chunk_size=5, overlap=0) == []


# ---------------------------------------------------------------- vector_search
class TestVectorSearch:
    def _make_embeddings(self, n: int, dim: int = 4):
        rng = np.random.default_rng(42)
        return rng.random((n, dim))

    def test_returns_top_k(self, monkeypatch):
        chunks = [f"chunk{i}" for i in range(10)]
        embeddings = self._make_embeddings(10)

        def fake_embeddings(query):
            return np.ones((1, 4))

        monkeypatch.setattr(
            "scratchagent.rag.get_embeddings", fake_embeddings
        )
        results = vector_search("query", chunks, embeddings, top_k=3)
        assert len(results) == 3

    def test_empty_index_raises(self, monkeypatch):
        """空 chunks 时 cosine_similarity 对空矩阵抛 ValueError（源码未做空保护）。"""
        monkeypatch.setattr(
            "scratchagent.rag.get_embeddings",
            lambda q: np.ones((1, 4)),
        )
        import pytest

        with pytest.raises(ValueError):
            vector_search("query", [], np.zeros((0, 4)), top_k=3)

    def test_result_keys(self, monkeypatch):
        chunks = [f"chunk{i}" for i in range(5)]
        embeddings = self._make_embeddings(5)
        monkeypatch.setattr(
            "scratchagent.rag.get_embeddings",
            lambda q: np.ones((1, 4)),
        )
        results = vector_search("query", chunks, embeddings, top_k=2)
        for r in results:
            assert "chunk" in r
            assert "similarity" in r
            assert isinstance(r["similarity"], float)

    def test_similarity_desc_order(self, monkeypatch):
        # 构造与 query 最相似的向量排在前
        chunks = ["a", "b", "c", "d"]
        embeddings = np.array(
            [
                [0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.5],
                [0.0, 0.0, 0.0, 0.9],
                [0.0, 0.0, 0.0, 0.2],
            ]
        )
        query_emb = np.array([[0.0, 0.0, 0.0, 1.0]])

        monkeypatch.setattr(
            "scratchagent.rag.get_embeddings", lambda q: query_emb
        )
        results = vector_search("query", chunks, embeddings, top_k=3)
        sims = [r["similarity"] for r in results]
        assert sims == sorted(sims, reverse=True)
