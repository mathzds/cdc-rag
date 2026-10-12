import config
from cli import CASE_USAGE, build_rag, index
from repositories.sqlite_db import SqliteQuestionLog, SqliteTestCases, connect


def test_search():
    db = connect(config.DB_PATH)
    cases = SqliteTestCases(db).all()
    assert cases, "nenhum caso de teste no banco. " + CASE_USAGE
    rag = build_rag(SqliteQuestionLog(db))
    if not rag.is_indexed():
        index(rag)
    for question, expected in cases:
        got = [a.id for a in rag.search(question)]
        assert expected in got, (question, expected, got)


if __name__ == "__main__":
    test_search()
    print("ok")
