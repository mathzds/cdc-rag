import re
import sys

import config
from domain.models import ServiceError
from domain.rag import Rag
from infra.ollama import OllamaClient
from infra.planalto import PlanaltoSource
from repositories.numpy_store import NumpyStore
from repositories.sqlite_db import SqliteQuestionLog, SqliteTestCases, connect

CASE_USAGE = 'Uso: cdc-rag caso "pergunta" "Art. 26"'


def build_rag(log: SqliteQuestionLog) -> Rag:
    ollama = OllamaClient(
        config.OLLAMA_URL, config.EMBED_MODEL, config.CHAT_MODEL, config.THINK, config.NUM_CTX
    )
    return Rag(ollama, ollama, NumpyStore(config.DATA_DIR), log, config.TOP_K)


def index(rag: Rag) -> None:
    print("Indexando o CDC...")
    n = rag.index(PlanaltoSource(config.CDC_URL, config.DATA_DIR / "cdc.htm"))
    print(f"{n} artigos indexados.")


def ask(rag: Rag, question: str) -> None:
    found, chunks = rag.answer(question)
    for chunk in chunks:
        print(chunk, end="", flush=True)
    print("\n\nFontes: " + ", ".join(a.id for a in found) + " do CDC")


def chat(rag: Rag) -> None:
    print("Pergunte sobre o CDC (Ctrl+D para sair).")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question:
            ask(rag, question)


def history(log: SqliteQuestionLog) -> None:
    for q in reversed(log.latest(10)):
        print(f"{q['asked_at']}  {q['question']}\n                     {q['sources']}")


def web(rag: Rag, log: SqliteQuestionLog) -> None:
    import uvicorn

    from web.api import create_app

    print("Abra http://127.0.0.1:8000 no navegador (Ctrl+C para parar).")
    uvicorn.run(create_app(rag, log), host="127.0.0.1", port=8000, log_level="warning")


def add_case(cases: SqliteTestCases, args: list[str]) -> None:
    if len(args) != 2 or not re.fullmatch(r"Art\. \d+(-[A-Z])?", args[1]):
        sys.exit(CASE_USAGE)
    cases.add(args[0], args[1])
    print(f"Caso adicionado: {args[0]!r} -> {args[1]}")


def main() -> None:
    argv = sys.argv[1:]
    db = connect(config.DB_PATH)
    log = SqliteQuestionLog(db)
    if argv == ["historico"]:
        return history(log)
    if argv[:1] == ["caso"]:
        return add_case(SqliteTestCases(db), argv[1:])
    rag = build_rag(log)
    try:
        if argv == ["index"]:
            return index(rag)
        if not rag.is_indexed():
            index(rag)
        if argv == ["web"]:
            return web(rag, log)
        if argv:
            return ask(rag, " ".join(argv))
        chat(rag)
    except ServiceError as e:
        sys.exit(str(e))
