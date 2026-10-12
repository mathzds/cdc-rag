import json
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from domain.models import ServiceError
from domain.rag import Rag
from repositories.sqlite_db import SqliteQuestionLog

STATIC = Path(__file__).parent / "static"


class Question(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=1000)


def ndjson(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False) + "\n"


def create_app(rag: Rag, log: SqliteQuestionLog) -> FastAPI:
    app = FastAPI(title="Direitos do Consumidor")
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/", include_in_schema=False)
    def page():
        return FileResponse(STATIC / "index.html")

    @app.get("/api/articles")
    def articles():
        return [asdict(a) for a in rag.articles()]

    @app.get("/api/history")
    def history():
        return log.latest(20)

    @app.post("/api/ask")
    def ask(body: Question):
        try:
            found, chunks = rag.answer(body.question)
        except ServiceError as e:
            raise HTTPException(503, str(e)) from e

        def lines():
            yield ndjson({"sources": [a.id for a in found]})
            try:
                for chunk in chunks:
                    yield ndjson({"chunk": chunk})
            except ServiceError as e:
                yield ndjson({"error": str(e)})

        return StreamingResponse(lines(), media_type="application/x-ndjson")

    return app
