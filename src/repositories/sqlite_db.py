import sqlite3
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    asked_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS test_cases (
    question TEXT PRIMARY KEY,
    expected TEXT NOT NULL
);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, check_same_thread=False)
    db.executescript(SCHEMA)
    return db


@dataclass
class SqliteQuestionLog:
    db: sqlite3.Connection

    def record(self, question: str, answer: str, sources: list[str]) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO questions (question, answer, sources) VALUES (?, ?, ?)",
                (question, answer, ", ".join(sources)),
            )

    def latest(self, n: int) -> list[dict]:
        cur = self.db.execute("SELECT * FROM questions ORDER BY id DESC LIMIT ?", (n,))
        columns = [c[0] for c in cur.description]
        return [dict(zip(columns, row)) for row in cur]


@dataclass
class SqliteTestCases:
    db: sqlite3.Connection

    def all(self) -> list[tuple[str, str]]:
        return self.db.execute("SELECT question, expected FROM test_cases ORDER BY rowid").fetchall()

    def add(self, question: str, expected: str) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO test_cases VALUES (?, ?)", (question, expected))
