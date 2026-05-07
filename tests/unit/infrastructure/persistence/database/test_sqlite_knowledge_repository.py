from infrastructure.persistence.database.sqlite_knowledge_repository import SqliteKnowledgeRepository


def test_chapter_number_from_fact_accepts_chapter_id_fallback():
    assert SqliteKnowledgeRepository._chapter_number_from_fact({"chapter_id": "12"}) == 12


def test_chapter_number_from_fact_prefers_chapter_number():
    assert SqliteKnowledgeRepository._chapter_number_from_fact({"chapter_number": "7", "chapter_id": "12"}) == 7
