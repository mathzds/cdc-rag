import html
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from domain.models import Article, ServiceError


@dataclass
class PlanaltoSource:
    url: str
    cache: Path

    def articles(self) -> list[Article]:
        if not self.cache.exists():
            self.cache.parent.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(self.url, headers={"User-Agent": "Mozilla/5.0"})
            try:
                self.cache.write_bytes(urllib.request.urlopen(req, timeout=60).read())
            except OSError as e:
                raise ServiceError(f"Não consegui baixar a lei do Planalto: {e}") from e
        return split_articles(self.cache.read_text(encoding="cp1252"))


def split_articles(page: str) -> list[Article]:
    t = re.sub(r"<(script|style|strike)\b.*?</\1>", " ", page, flags=re.S | re.I)
    t = re.sub(r"<p[^>]*center.*?</p>", " ", t, flags=re.S | re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.split(r"Brasília, \d+ de \w+ de \d{4}", re.sub(r"\s+", " ", t))[0]
    arts = []
    for part in re.split(r'(?<!["“])\b(?=Art\.\s*\d)', t)[1:]:
        text = part.strip()
        if len(text) < 40 and "(Vetado)" in text:
            continue
        num = re.match(r"Art\.\s*(\d+(?:-[A-Z])?)", text).group(1)
        arts.append(Article("Art. " + num, text))
    return arts
