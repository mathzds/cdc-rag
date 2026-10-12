from domain.models import ServiceError
from domain.rag import Rag
from tests.fakes import FakeChat, FakeEmbedder, FakeLog, FakeSource, FakeStore


def test_index():
    store = FakeStore()
    rag = Rag(FakeEmbedder(), FakeChat(), store, FakeLog(), top_k=2)
    assert not rag.is_indexed()
    assert rag.index(FakeSource(120)) == 120
    assert rag.is_indexed()
    assert len(store.saved[0]) == len(store.saved[1]) == 120


def test_index_rejects_broken_source():
    rag = Rag(FakeEmbedder(), FakeChat(), FakeStore(), FakeLog(), top_k=2)
    try:
        rag.index(FakeSource(5))
    except ServiceError:
        return
    raise AssertionError("aceitou fonte com só 5 artigos")


def test_answer_searches_with_rewritten_question():
    embedder, chat = FakeEmbedder(), FakeChat()
    rag = Rag(embedder, chat, FakeStore(), FakeLog(), top_k=2)
    rag.index(FakeSource(120))
    found, chunks = rag.answer("venda casada?")
    assert embedder.calls[-1] == ["venda casada? termos jurídicos"], embedder.calls[-1]
    assert [a.id for a in found] == ["Art. 1", "Art. 2"]
    assert list(chunks) == ["resposta"]
    assert "Art. 1. Texto 1." in chat.prompts[0], chat.prompts[0]
    assert chat.prompts[0].endswith("Pergunta: venda casada?"), chat.prompts[0]


def test_answer_is_recorded_only_after_stream_ends():
    log = FakeLog()
    rag = Rag(FakeEmbedder(), FakeChat(), FakeStore(), log, top_k=2)
    rag.index(FakeSource(120))
    _, chunks = rag.answer("venda casada?")
    assert log.records == []
    list(chunks)
    assert log.records == [("venda casada?", "resposta", ["Art. 1", "Art. 2"])], log.records


if __name__ == "__main__":
    test_index()
    test_index_rejects_broken_source()
    test_answer_searches_with_rewritten_question()
    test_answer_is_recorded_only_after_stream_ends()
    print("ok")
