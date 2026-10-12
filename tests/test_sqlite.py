from pathlib import Path

from repositories.sqlite_db import SqliteQuestionLog, SqliteTestCases, connect


def test_roundtrip():
    db = connect(Path(":memory:"))

    log = SqliteQuestionLog(db)
    log.record("pergunta?", "resposta", ["Art. 49", "Art. 26"])
    [item] = log.latest(10)
    assert item["question"] == "pergunta?", item
    assert item["answer"] == "resposta", item
    assert item["sources"] == "Art. 49, Art. 26", item

    cases = SqliteTestCases(db)
    cases.add("q1", "Art. 1")
    cases.add("q1", "Art. 2")
    assert cases.all() == [("q1", "Art. 2")], cases.all()


if __name__ == "__main__":
    test_roundtrip()
    print("ok")
