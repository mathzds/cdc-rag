import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterator

from domain.models import ServiceError


@dataclass
class OllamaClient:
    url: str
    embed_model: str
    chat_model: str
    think: bool
    num_ctx: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._post("/api/embed", {"model": self.embed_model, "input": texts})["embeddings"]

    def complete(self, system: str, user: str) -> str:
        body = self._chat_body(system, user, stream=False)
        body["options"]["temperature"] = 0
        return self._post("/api/chat", body)["message"]["content"]

    def stream(self, system: str, user: str) -> Iterator[str]:
        with self._open("/api/chat", self._chat_body(system, user, stream=True)) as resp:
            for line in resp:
                yield json.loads(line)["message"]["content"]

    def _chat_body(self, system: str, user: str, stream: bool) -> dict:
        return {
            "model": self.chat_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": stream,
            "think": self.think,
            "options": {"num_ctx": self.num_ctx},
        }

    def _post(self, path: str, body: dict) -> dict:
        with self._open(path, body) as resp:
            return json.load(resp)

    def _open(self, path: str, body: dict):
        req = urllib.request.Request(
            self.url + path, json.dumps(body).encode(), {"Content-Type": "application/json"}
        )
        try:
            return urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            raise ServiceError(
                f"Erro do Ollama: {e.read().decode()}. Baixou o modelo? ollama pull {body['model']}"
            ) from e
        except urllib.error.URLError as e:
            raise ServiceError("Ollama não está rodando. Inicie com: ollama serve") from e
