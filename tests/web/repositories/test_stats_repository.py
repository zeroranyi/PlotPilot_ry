"""Tests for StatsRepository."""
import pytest
from pathlib import Path
from web.repositories.stats_repository import StatsRepository


@pytest.fixture
def temp_books_dir(tmp_path: Path):
    """Create a temporary books directory structure for testing."""
    books_dir = tmp_path / "books"
    books_dir.mkdir()

    # Create test book 1
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
            {"id": 2, "title": "Chapter 2"}
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

    # Create test book 2 (only manifest, no chapters)
    book2 = books_dir / "test-book-2"
    book2.mkdir()
    manifest_data2 = {
        "title": "Test Book 2",
        "stage": "published"
    }
    (book2 / "manifest.json").write_text(json.dumps(manifest_data2, ensure_ascii=False))

    return books_dir


def test_get_all_book_slugs(temp_books_dir: Path):
    """Test getting all book slugs from manifest.json files."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")

    slugs = repo.get_all_book_slugs()

    assert isinstance(slugs, list)
    assert len(slugs) == 2
    assert "test-book-1" in slugs
    assert "test-book-2" in slugs


def test_get_book_manifest(temp_books_dir: Path):
    """Test reading a book's manifest.json."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")

    manifest = repo.get_book_manifest("test-book-1")

    assert manifest is not None
    assert isinstance(manifest, dict)
    assert manifest["title"] == "Test Book 1"
    assert manifest["stage"] == "draft"


def test_get_book_manifest_nonexistent(temp_books_dir: Path):
    """Test reading manifest for nonexistent book."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")

    manifest = repo.get_book_manifest("nonexistent-book")

    assert manifest is None


def test_get_book_outline(temp_books_dir: Path):
    """Test reading a book's outline.json."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")

    outline = repo.get_book_outline("test-book-1")

    assert outline is not None
    assert isinstance(outline, dict)
    assert "chapters" in outline
    assert len(outline["chapters"]) == 2
    assert outline["chapters"][0]["title"] == "Chapter 1"


def test_get_book_outline_nonexistent(temp_books_dir: Path):
    """Test reading outline for nonexistent book."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")

    outline = repo.get_book_outline("nonexistent-book")

    assert outline is None


def test_get_chapter_content(temp_books_dir: Path):
    """Test reading chapter content."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")

    content = repo.get_chapter_content("test-book-1", 1)

    assert content is not None
    assert isinstance(content, str)
    assert "test content for chapter 1" in content


def test_get_chapter_content_mixed_text(temp_books_dir: Path):
    """Test reading chapter content with mixed Chinese and English."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")

    content = repo.get_chapter_content("test-book-1", 2)

    assert content is not None
    assert isinstance(content, str)
    assert "中文" in content
    assert "English" in content


def test_get_chapter_content_nonexistent(temp_books_dir: Path):
    """Test reading content for nonexistent chapter."""
    books_root = temp_books_dir.parent
    repo = StatsRepository(books_root / "books")

    content = repo.get_chapter_content("test-book-1", 99)

    assert content is None


def test_count_words_english():
    """Test word counting for English text."""
    repo = StatsRepository(Path("/tmp/books"))

    text = "This is a simple English sentence with seven words."
    count = repo.count_words(text)

    assert count == 9  # English words


def test_count_words_chinese():
    """Test word counting for Chinese text."""
    repo = StatsRepository(Path("/tmp/books"))

    text = "这是一个简单的中文句子，包含七个汉字。"
    count = repo.count_words(text)

    assert count == 17  # Each Chinese character counts as one word


def test_count_words_mixed():
    """Test word counting for mixed Chinese and English text."""
    repo = StatsRepository(Path("/tmp/books"))

    text = "This is English. 这是中文。Mixed text 混合文本。"
    count = repo.count_words(text)

    # "This is English." = 3 English words
    # "这是中文。" = 4 Chinese characters
    # "Mixed text" = 2 English words
    # "混合文本。" = 4 Chinese characters
    # Total = 3 + 4 + 2 + 4 = 13
    assert count == 13


def test_count_words_empty():
    """Test word counting for empty text."""
    repo = StatsRepository(Path("/tmp/books"))

    text = ""
    count = repo.count_words(text)

    assert count == 0


def test_count_words_whitespace_only():
    """Test word counting for whitespace-only text."""
    repo = StatsRepository(Path("/tmp/books"))

    text = "   \n\t  "
    count = repo.count_words(text)

    assert count == 0
