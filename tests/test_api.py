import json
from pathlib import Path

from fastapi.testclient import TestClient

from domain.models import ServiceError
from domain.rag import Rag
from repositories.sqlite_db import SqliteQuestionLog, connect
from tests.fakes import FakeChat, FakeEmbedder, FakeSource, FakeStore
from web.api import create_app


class OfflineChat(FakeChat):
    def complete(self, system, user):
        raise ServiceError("Ollama não está rodando. Inicie com: ollama serve")


class BrokenStreamChat(FakeChat):
    def stream(self, system, user):
        yield "começo"
        raise ServiceError("conexão caiu")


def client(chat=None):
    log = SqliteQuestionLog(connect(Path(":memory:")))
    rag = Rag(FakeEmbedder(), chat or FakeChat(), FakeStore(), log, top_k=2)
    rag.index(FakeSource(120))
    return TestClient(create_app(rag, log))


def lines(response):
    return [json.loads(line) for line in response.text.splitlines()]


def test_page_and_articles():
    c = client()
    page = c.get("/")
    assert page.status_code == 200 and "<html" in page.text
    script = c.get("/static/app.js")
    assert script.status_code == 200 and "javascript" in script.headers["content-type"], script
    style = c.get("/static/style.css")
    assert style.status_code == 200 and "text/css" in style.headers["content-type"], style
    articles = c.get("/api/articles").json()
    assert len(articles) == 120 and articles[0] == {"id": "Art. 1", "text": "Art. 1. Texto 1."}


def test_ask_streams_and_records():
    c = client()
    response = c.post("/api/ask", json={"question": "  venda casada?  "})
    assert response.status_code == 200, response.text
    assert lines(response) == [{"sources": ["Art. 1", "Art. 2"]}, {"chunk": "resposta"}]
    [item] = c.get("/api/history").json()
    assert item["question"] == "venda casada?", item
    assert item["answer"] == "resposta" and item["sources"] == "Art. 1, Art. 2", item


def test_ask_rejects_blank_question():
    assert client().post("/api/ask", json={"question": "   "}).status_code == 422


def test_ask_offline_is_503():
    response = client(OfflineChat()).post("/api/ask", json={"question": "oi"})
    assert response.status_code == 503, response.text
    assert "ollama serve" in response.json()["detail"]


def test_ask_error_mid_stream():
    c = client(BrokenStreamChat())
    got = lines(c.post("/api/ask", json={"question": "oi"}))
    assert got[1:] == [{"chunk": "começo"}, {"error": "conexão caiu"}], got
    assert c.get("/api/history").json() == []


if __name__ == "__main__":
    test_page_and_articles()
    test_ask_streams_and_records()
    test_ask_rejects_blank_question()
    test_ask_offline_is_503()
    test_ask_error_mid_stream()
    print("ok")
