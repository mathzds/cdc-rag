from dataclasses import dataclass
from typing import Iterator

from domain.interfaces import ArticleStore, ChatModel, Embedder, LawSource, QuestionLog
from domain.models import Article, ServiceError

MIN_ARTICLES = 100

SYSTEM = (
    "Você é assistente sobre o Código de Defesa do Consumidor (Lei 8.078/1990). "
    "Responda em português, claro e direto, usando apenas os artigos fornecidos. "
    "Cite os artigos (ex.: 'art. 49 do CDC'). Se os artigos não respondem à pergunta, "
    "diga que não encontrou base no CDC. Não invente artigos."
)
REWRITE = (
    "Reescreva a pergunta do consumidor usando os termos técnicos que o Código de Defesa "
    "do Consumidor usaria. Responda só com a pergunta reescrita, em uma frase."
)


@dataclass
class Rag:
    embedder: Embedder
    chat: ChatModel
    store: ArticleStore
    log: QuestionLog
    top_k: int

    def is_indexed(self) -> bool:
        return self.store.exists()

    def articles(self) -> list[Article]:
        return self.store.all()

    def index(self, source: LawSource) -> int:
        articles = source.articles()
        if len(articles) < MIN_ARTICLES:
            raise ServiceError(f"Só {len(articles)} artigos extraídos; o layout da fonte mudou?")
        self.store.save(articles, self.embedder.embed([a.text for a in articles]))
        return len(articles)

    def search(self, question: str) -> list[Article]:
        legal = self.chat.complete(REWRITE, question)
        return self.store.search(self.embedder.embed([question + " " + legal])[0], self.top_k)

    def answer(self, question: str) -> tuple[list[Article], Iterator[str]]:
        found = self.search(question)
        context = "\n\n".join(a.text for a in found)
        chunks = self.chat.stream(SYSTEM, f"Artigos:\n{context}\n\nPergunta: {question}")
        return found, self._recorded(question, found, chunks)

    def _recorded(self, question: str, found: list[Article], chunks: Iterator[str]) -> Iterator[str]:
        parts = []
        for chunk in chunks:
            parts.append(chunk)
            yield chunk
        self.log.record(question, "".join(parts), [a.id for a in found])
