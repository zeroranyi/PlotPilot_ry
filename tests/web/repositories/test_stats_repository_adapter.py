"""Tests for StatsRepositoryAdapter"""
import pytest
from pathlib import Path
import json
import tempfile
import shutil

from web.repositories.stats_repository_adapter import StatsRepositoryAdapter


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory with test novels."""
    temp_dir = tempfile.mkdtemp()
    data_path = Path(temp_dir)
    novels_dir = data_path / "novels"
    novels_dir.mkdir(parents=True)

    # Create test novel 1
    novel1 = {
        "id": "test-novel-1",
        "title": "测试小说1",
        "author": "作者1",
        "target_chapters": 10,
        "stage": "writing",
        "chapters": [
            {
                "id": "ch-1",
                "number": 1,
                "title": "第一章",
                "content": "这是第一章的内容。Hello world!",
                "status": "completed"
            },
            {
                "id": "ch-2",
                "number": 2,
                "title": "第二章",
                "content": "这是第二章的内容。",
                "status": "draft"
            }
        ]
    }

    # Create test novel 2
    novel2 = {
        "id": "test-novel-2",
        "title": "测试小说2",
        "author": "作者2",
        "target_chapters": 5,
        "stage": "planning",
        "chapters": []
    }

    with open(novels_dir / "test-novel-1.json", 'w', encoding='utf-8') as f:
        json.dump(novel1, f, ensure_ascii=False, indent=2)

    with open(novels_dir / "test-novel-2.json", 'w', encoding='utf-8') as f:
        json.dump(novel2, f, ensure_ascii=False, indent=2)

    yield data_path

    # Cleanup
    shutil.rmtree(temp_dir)


class TestStatsRepositoryAdapter:
    """Test suite for StatsRepositoryAdapter"""

    def test_get_all_book_slugs(self, temp_data_dir):
        """Test getting all book slugs"""
        adapter = StatsRepositoryAdapter(temp_data_dir)
        slugs = adapter.get_all_book_slugs()

        assert len(slugs) == 2
        assert "test-novel-1" in slugs
        assert "test-novel-2" in slugs

    def test_get_all_book_slugs_empty_directory(self):
        """Test getting slugs from empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = StatsRepositoryAdapter(Path(temp_dir))
            slugs = adapter.get_all_book_slugs()
            assert slugs == []

    def test_get_book_manifest(self, temp_data_dir):
        """Test reading book manifest"""
        adapter = StatsRepositoryAdapter(temp_data_dir)
        manifest = adapter.get_book_manifest("test-novel-1")

        assert manifest is not None
        assert manifest["title"] == "测试小说1"
        assert manifest["author"] == "作者1"
        assert manifest["slug"] == "test-novel-1"
        assert manifest["stage"] == "writing"
        assert manifest["target_chapters"] == 10
        assert len(manifest["chapters"]) == 2

    def test_get_book_manifest_not_found(self, temp_data_dir):
        """Test reading non-existent book"""
        adapter = StatsRepositoryAdapter(temp_data_dir)
        manifest = adapter.get_book_manifest("non-existent")

        assert manifest is None

    def test_get_chapter_content(self, temp_data_dir):
        """Test reading chapter content"""
        adapter = StatsRepositoryAdapter(temp_data_dir)
        content = adapter.get_chapter_content("test-novel-1", 1)

        assert content is not None
        assert "第一章的内容" in content
        assert "Hello world" in content

    def test_get_chapter_content_not_found(self, temp_data_dir):
        """Test reading non-existent chapter"""
        adapter = StatsRepositoryAdapter(temp_data_dir)
        content = adapter.get_chapter_content("test-novel-1", 999)

        assert content is None

    def test_get_chapter_content_book_not_found(self, temp_data_dir):
        """Test reading chapter from non-existent book"""
        adapter = StatsRepositoryAdapter(temp_data_dir)
        content = adapter.get_chapter_content("non-existent", 1)

        assert content is None

    def test_count_words_chinese(self, temp_data_dir):
        """Test word counting for Chinese text"""
        adapter = StatsRepositoryAdapter(temp_data_dir)
        count = adapter.count_words("这是一个测试")

        assert count == 6  # 6 Chinese characters

    def test_count_words_english(self, temp_data_dir):
        """Test word counting for English text"""
        adapter = StatsRepositoryAdapter(temp_data_dir)
        count = adapter.count_words("Hello world test")

        assert count == 3  # 3 English words

    def test_count_words_mixed(self, temp_data_dir):
        """Test word counting for mixed Chinese and English"""
        adapter = StatsRepositoryAdapter(temp_data_dir)
        count = adapter.count_words("这是测试 Hello world")

        assert count == 6  # 4 Chinese + 2 English

    def test_count_words_empty(self, temp_data_dir):
        """Test word counting for empty text"""
        adapter = StatsRepositoryAdapter(temp_data_dir)
        count = adapter.count_words("")

        assert count == 0

    def test_get_book_outline(self, temp_data_dir):
        """Outline is derived from novel JSON chapters for StatsService."""
        adapter = StatsRepositoryAdapter(temp_data_dir)
        outline = adapter.get_book_outline("test-novel-1")

        assert outline is not None
        assert "chapters" in outline
        assert len(outline["chapters"]) == 2
        assert outline["chapters"][0]["id"] == 1
        assert outline["chapters"][0]["title"] == "第一章"
        assert outline["chapters"][1]["id"] == 2

    def test_get_book_outline_empty_chapters(self, temp_data_dir):
        adapter = StatsRepositoryAdapter(temp_data_dir)
        outline = adapter.get_book_outline("test-novel-2")
        assert outline is not None
        assert outline["chapters"] == []
