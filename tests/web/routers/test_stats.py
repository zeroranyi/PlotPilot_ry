"""Tests for statistics API router."""
import pytest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

from web.repositories.stats_repository import StatsRepository
from web.services.stats_service import StatsService
from web.routers.stats import create_stats_router


@pytest.fixture
def temp_books_dir(tmp_path: Path):
    """Create a temporary books directory structure for testing."""
    books_dir = tmp_path / "books"
    books_dir.mkdir()

    # Create test book with content
    book = books_dir / "test-book"
    book.mkdir()

    # Create manifest.json
    import json
    manifest_data = {
        "title": "Test Book",
        "stage": "draft"
    }
    (book / "manifest.json").write_text(json.dumps(manifest_data, ensure_ascii=False))

    # Create outline.json
    outline_data = {
        "chapters": [
            {"id": 1, "title": "Chapter 1"},
            {"id": 2, "title": "Chapter 2"}
        ]
    }
    (book / "outline.json").write_text(json.dumps(outline_data, ensure_ascii=False))

    # Create chapters directory and chapter files
    chapters_dir = book / "chapters"
    chapters_dir.mkdir()

    ch1_dir = chapters_dir / "ch-0001"
    ch1_dir.mkdir()
    (ch1_dir / "body.md").write_text("This is test content for chapter 1.", encoding='utf-8')

    ch2_dir = chapters_dir / "ch-0002"
    ch2_dir.mkdir()
    (ch2_dir / "body.md").write_text("This is chapter 2 content.", encoding='utf-8')

    return books_dir


@pytest.fixture
def test_app(temp_books_dir: Path):
    """Create a test FastAPI app with stats router."""
    # Create app and add error handlers
    from web.middleware.error_handler import add_error_handlers
    app = FastAPI()
    add_error_handlers(app)

    # Create stats service and router
    books_root = temp_books_dir.parent / "books"
    repo = StatsRepository(books_root)
    service = StatsService(repo)
    router = create_stats_router(service)

    # Include router with /api/stats prefix
    app.include_router(router, prefix="/api/stats", tags=["statistics"])

    return app


class TestGetGlobalStats:
    """Tests for GET /api/stats/global endpoint."""

    def test_get_global_stats(self, test_app: FastAPI):
        """Test getting global statistics."""
        client = TestClient(test_app)
        response = client.get("/api/stats/global")

        assert response.status_code == 200
        data = response.json()

        # Verify SuccessResponse structure
        assert data["success"] is True
        assert "data" in data

        # Verify GlobalStats structure
        stats = data["data"]
        assert stats["total_books"] == 1
        assert stats["total_chapters"] == 2
        assert stats["total_words"] > 0
        assert stats["total_characters"] > 0
        assert "draft" in stats["books_by_stage"]
        assert stats["books_by_stage"]["draft"] == 1


class TestGetBookStats:
    """Tests for GET /api/stats/book/{slug} endpoint."""

    def test_get_book_stats(self, test_app: FastAPI):
        """Test getting book statistics."""
        client = TestClient(test_app)
        response = client.get("/api/stats/book/test-book")

        assert response.status_code == 200
        data = response.json()

        # Verify SuccessResponse structure
        assert data["success"] is True
        assert "data" in data

        # Verify BookStats structure
        stats = data["data"]
        assert stats["slug"] == "test-book"
        assert stats["title"] == "Test Book"
        assert stats["total_chapters"] == 2
        assert stats["total_words"] > 0
        assert stats["avg_chapter_words"] > 0
        assert 0.0 <= stats["completion_rate"] <= 1.0
        assert "last_updated" in stats

    def test_get_book_stats_not_found(self, test_app: FastAPI):
        """Test getting statistics for nonexistent book."""
        client = TestClient(test_app)
        response = client.get("/api/stats/book/nonexistent-book")

        assert response.status_code == 404
        data = response.json()

        # Verify ErrorResponse structure
        assert data["success"] is False
        assert data["code"] == "NOT_FOUND"
        assert "not found" in data["message"].lower()


class TestGetChapterStats:
    """Tests for GET /api/stats/book/{slug}/chapter/{chapter_id} endpoint."""

    def test_get_chapter_stats(self, test_app: FastAPI):
        """Test getting chapter statistics."""
        client = TestClient(test_app)
        response = client.get("/api/stats/book/test-book/chapter/1")

        assert response.status_code == 200
        data = response.json()

        # Verify SuccessResponse structure
        assert data["success"] is True
        assert "data" in data

        # Verify ChapterStats structure
        stats = data["data"]
        assert stats["chapter_id"] == 1
        assert stats["title"] == "Chapter 1"
        assert stats["word_count"] > 0
        assert stats["character_count"] > 0
        assert stats["paragraph_count"] > 0
        assert stats["has_content"] is True

    def test_get_chapter_stats_not_found(self, test_app: FastAPI):
        """Test getting statistics for nonexistent chapter."""
        client = TestClient(test_app)
        response = client.get("/api/stats/book/test-book/chapter/99")

        assert response.status_code == 404
        data = response.json()

        # Verify ErrorResponse structure
        assert data["success"] is False
        assert data["code"] == "NOT_FOUND"
        assert "not found" in data["message"].lower()


class TestGetWritingProgress:
    """Tests for GET /api/stats/book/{slug}/progress endpoint."""

    def test_get_writing_progress(self, test_app: FastAPI):
        """Test getting writing progress."""
        client = TestClient(test_app)
        response = client.get("/api/stats/book/test-book/progress?days=30")

        assert response.status_code == 200
        data = response.json()

        # Verify SuccessResponse structure
        assert data["success"] is True
        assert "data" in data

        # Verify empty list for now (Week 2 feature)
        progress_list = data["data"]
        assert isinstance(progress_list, list)
        assert len(progress_list) == 0

    def test_get_writing_progress_default_days(self, test_app: FastAPI):
        """Test getting writing progress with default days parameter."""
        client = TestClient(test_app)
        response = client.get("/api/stats/book/test-book/progress")

        assert response.status_code == 200
        data = response.json()

        # Should use default of 30 days
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_writing_progress_invalid_days(self, test_app: FastAPI):
        """Test validation of days parameter."""
        client = TestClient(test_app)

        # Test days < 1 (should fail validation)
        response = client.get("/api/stats/book/test-book/progress?days=0")
        assert response.status_code == 422

        # Test days > 365 (should fail validation)
        response = client.get("/api/stats/book/test-book/progress?days=366")
        assert response.status_code == 422

    def test_get_writing_progress_book_not_found(self, test_app: FastAPI):
        """Test getting writing progress for nonexistent book."""
        client = TestClient(test_app)
        response = client.get("/api/stats/book/nonexistent-book/progress")

        assert response.status_code == 404
        data = response.json()

        # Verify ErrorResponse structure
        assert data["success"] is False
        assert data["code"] == "NOT_FOUND"
        assert "not found" in data["message"].lower()
