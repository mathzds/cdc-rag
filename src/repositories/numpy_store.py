import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from domain.models import Article


class NumpyStore:
    def __init__(self, folder: Path):
        self.articles_path = folder / "articles.json"
        self.vectors_path = folder / "vectors.npy"
        self._loaded = None

    def exists(self) -> bool:
        return self.vectors_path.exists()

    def all(self) -> list[Article]:
        return list(self._load()[0])

    def save(self, articles: list[Article], vectors: list[list[float]]) -> None:
        self.vectors_path.parent.mkdir(parents=True, exist_ok=True)
        v = np.array(vectors, dtype=np.float32)
        np.save(self.vectors_path, v / np.linalg.norm(v, axis=1, keepdims=True))
        data = [asdict(a) for a in articles]
        self.articles_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        self._loaded = None

    def search(self, vector: list[float], k: int) -> list[Article]:
        articles, vectors = self._load()
        scores = vectors @ np.array(vector, dtype=np.float32)
        return [articles[i] for i in np.argsort(-scores)[:k]]

    def _load(self):
        if self._loaded is None:
            data = json.loads(self.articles_path.read_text(encoding="utf-8"))
            self._loaded = [Article(**d) for d in data], np.load(self.vectors_path)
        return self._loaded
