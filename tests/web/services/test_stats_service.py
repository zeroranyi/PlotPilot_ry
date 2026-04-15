"""Tests for StatsService."""
import pytest
from pathlib import Path
from datetime import datetime
from web.repositories.stats_repository import StatsRepository
from web.services.stats_service import StatsService
from web.models.stats_models import GlobalStats, BookStats, ChapterStats, WritingProgress


@pytest.fixture
def temp_books_dir(tmp_path: Path):
    """Create a temporary books directory structure for testing."""
    books_dir = tmp_path / "books"
    books_dir.mkdir()

    # Create test book 1 with content
    book1 = books_dir / "test-book-1"
    book1.mkdir()

    # Create manifest.json
    manifest_data = {
        "title": "Test Book 1",
        "stage": "draft"
    }
    import json
    (book1 / "manifest.json").write_text(json.dumps(manifest_data, ensure_ascii=False))

    # Create outline.json
    outline_data = {
        "chapters": [
            {"id": 1, "title": "Chapter 1"},
            {"id": 2, "title": "Chapter 2"},
            {"id": 3, "title": "Chapter 3"}
        ]
    }
    (book1 / "outline.json").write_text(json.dumps(outline_data, ensure_ascii=False))

    # Create chapters directory and chapter files
    chapters_dir = book1 / "chapters"
    chapters_dir.mkdir()

    ch1_dir = chapters_dir / "ch-0001"
    ch1_dir.mkdir()
    (ch1_dir / "body.md").write_text("This is test content for chapter 1.", encoding='utf-8')

    ch2_dir = chapters_dir / "ch-0002"
    ch2_dir.mkdir()
    (ch2_dir / "body.md").write_text("这是第二章的内容，包含中文和English混合文本。", encoding='utf-8')

    ch3_dir = chapters_dir / "ch-0003"
    ch3_dir.mkdir()
    (ch3_dir / "body.md").write_text("", encoding='utf-8')

    # Create test book 2 (published stage)
    book2 = books_dir / "test-book-2"
    book2.mkdir()
    manifest_data2 = {
        "title": "Test Book 2",
        "stage": "published"
    }
    (book2 / "manifest.json").write_text(json.dumps(manifest_data2, ensure_ascii=False))

    outline_data2 = {
        "chapters": [
            {"id": 1, "title": "Single Chapter"}
        ]
    }
    (book2 / "outline.json").write_text(json.dumps(outline_data2, ensure_ascii=False))

    chapters_dir2 = book2 / "chapters"
    chapters_dir2.mkdir()

    ch1_dir2 = chapters_dir2 / "ch-0001"
    ch1_dir2.mkdir()
    (ch1_dir2 / "body.md").write_text("Content for book 2 chapter 1.", encoding='utf-8')

    return books_dir


def test_get_global_stats(temp_books_dir: Path):
    """Test getting global statistics across all books."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")
    service = StatsService(repo)

    stats = service.get_global_stats()

    assert isinstance(stats, GlobalStats)
    assert stats.total_books == 2
    assert stats.total_chapters == 4  # 3 in book1 + 1 in book2
    assert stats.total_words > 0
    assert stats.total_characters > 0
    assert "draft" in stats.books_by_stage
    assert stats.books_by_stage["draft"] == 1
    assert "published" in stats.books_by_stage
    assert stats.books_by_stage["published"] == 1


def test_get_book_stats(temp_books_dir: Path):
    """Test getting statistics for a single book."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")
    service = StatsService(repo)

    stats = service.get_book_stats("test-book-1")

    assert isinstance(stats, BookStats)
    assert stats.slug == "test-book-1"
    assert stats.title == "Test Book 1"
    assert stats.total_chapters == 3
    assert stats.total_words > 0
    assert stats.avg_chapter_words > 0
    assert 0.0 <= stats.completion_rate <= 1.0
    assert isinstance(stats.last_updated, datetime)


def test_get_book_stats_not_found(temp_books_dir: Path):
    """Test getting statistics for a nonexistent book."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")
    service = StatsService(repo)

    stats = service.get_book_stats("nonexistent-book")

    assert stats is None


def test_get_chapter_stats(temp_books_dir: Path):
    """Test getting statistics for a single chapter."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")
    service = StatsService(repo)

    stats = service.get_chapter_stats("test-book-1", 1)

    assert isinstance(stats, ChapterStats)
    assert stats.chapter_id == 1
    assert stats.title == "Chapter 1"
    assert stats.word_count > 0
    assert stats.character_count > 0
    assert stats.paragraph_count > 0
    assert stats.has_content is True


def test_get_chapter_stats_empty(temp_books_dir: Path):
    """Test getting statistics for an empty chapter."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")
    service = StatsService(repo)

    stats = service.get_chapter_stats("test-book-1", 3)

    assert isinstance(stats, ChapterStats)
    assert stats.chapter_id == 3
    assert stats.title == "Chapter 3"
    assert stats.word_count == 0
    assert stats.character_count == 0
    assert stats.paragraph_count == 0
    assert stats.has_content is False


def test_get_chapter_stats_not_found(temp_books_dir: Path):
    """Test getting statistics for a nonexistent chapter."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")
    service = StatsService(repo)

    stats = service.get_chapter_stats("test-book-1", 99)

    assert stats is None


def test_get_writing_progress(temp_books_dir: Path):
    """Test getting writing progress (currently returns empty list)."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")
    service = StatsService(repo)

    progress = service.get_writing_progress("test-book-1", days=30)

    assert isinstance(progress, list)
    assert len(progress) == 0
