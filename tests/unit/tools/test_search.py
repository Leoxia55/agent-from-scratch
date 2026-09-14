"""tools/_search.py 单元测试：Tavily 搜索工具。"""

from __future__ import annotations

from scratchagent.tools import search_web


class TestSearchWeb:
    def test_returns_results(self, monkeypatch):
        fake_results = [{"title": "t", "url": "u", "content": "c"}]

        class FakeClient:
            def __init__(self, api_key):
                pass

            def search(self, **kwargs):
                assert kwargs["query"] == "hello"
                return {"results": fake_results}

        monkeypatch.setattr("scratchagent.tools._search.TavilyClient", FakeClient)
        results = search_web("hello")
        assert results == fake_results

    def test_empty_results(self, monkeypatch):
        class FakeClient:
            def __init__(self, api_key):
                pass

            def search(self, **kwargs):
                return {"results": []}

        monkeypatch.setattr("scratchagent.tools._search.TavilyClient", FakeClient)
        assert search_web("nothing") == []

    def test_kwargs_passthrough(self, monkeypatch):
        captured = {}

        class FakeClient:
            def __init__(self, api_key):
                pass

            def search(self, **kwargs):
                captured.update(kwargs)
                return {"results": []}

        monkeypatch.setattr("scratchagent.tools._search.TavilyClient", FakeClient)
        search_web("q", max_results=3, topic="news", time_range="week")
        assert captured["max_results"] == 3
        assert captured["topic"] == "news"
        assert captured["time_range"] == "week"

    def test_time_range_omitted_when_none(self, monkeypatch):
        captured = {}

        class FakeClient:
            def __init__(self, api_key):
                pass

            def search(self, **kwargs):
                captured.update(kwargs)
                return {"results": []}

        monkeypatch.setattr("scratchagent.tools._search.TavilyClient", FakeClient)
        search_web("q")
        assert "time_range" not in captured
