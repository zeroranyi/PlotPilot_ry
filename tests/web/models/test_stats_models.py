"""Statistics data models tests."""
import pytest
from datetime import datetime
from pydantic import ValidationError


class TestGlobalStatsBasic:
    """Test GlobalStats model basic functionality."""

    def test_global_stats_basic(self):
        """Test GlobalStats can be created with valid data."""
        from aitext.web.models.stats_models import GlobalStats

        stats = GlobalStats(
            total_books=5,
            total_chapters=42,
            total_words=125000,
            total_characters=80000,
            books_by_stage={"planning": 2, "drafting": 2, "completed": 1}
        )

        assert stats.total_books == 5
        assert stats.total_chapters == 42
        assert stats.total_words == 125000
        assert stats.total_characters == 80000
        assert stats.books_by_stage == {"planning": 2, "drafting": 2, "completed": 1}

    def test_global_stats_empty_books_by_stage(self):
        """Test GlobalStats can be created with empty books_by_stage."""
        from aitext.web.models.stats_models import GlobalStats

        stats = GlobalStats(
            total_books=0,
            total_chapters=0,
            total_words=0,
            total_characters=0,
            books_by_stage={}
        )

        assert stats.total_books == 0
        assert stats.books_by_stage == {}

    def test_global_stats_with_zero_totals(self):
        """Test GlobalStats can be created with all zeros."""
        from aitext.web.models.stats_models import GlobalStats

        stats = GlobalStats(
            total_books=0,
            total_chapters=0,
            total_words=0,
            total_characters=0,
            books_by_stage={}
        )

        assert stats.total_books == 0
        assert stats.total_chapters == 0
        assert stats.total_words == 0
        assert stats.total_characters == 0


class TestBookStatsBasic:
    """Test BookStats model basic functionality."""

    def test_book_stats_basic(self):
        """Test BookStats can be created with valid data."""
        from aitext.web.models.stats_models import BookStats

        stats = BookStats(
            slug="my-novel",
            title="My Novel",
            total_chapters=20,
            completed_chapters=15,
            total_words=50000,
            avg_chapter_words=2500,
            completion_rate=0.75,
            last_updated=datetime(2024, 3, 15, 12, 0)
        )

        assert stats.slug == "my-novel"
        assert stats.title == "My Novel"
        assert stats.total_chapters == 20
        assert stats.completed_chapters == 15
        assert stats.total_words == 50000
        assert stats.avg_chapter_words == 2500
        assert stats.completion_rate == 0.75
        assert stats.last_updated == datetime(2024, 3, 15, 12, 0)

    def test_book_stats_completion_rate_edge_cases(self):
        """Test BookStats with edge case completion rates."""
        from aitext.web.models.stats_models import BookStats

        # Test with 0 completion rate
        stats_zero = BookStats(
            slug="new-book",
            title="New Book",
            total_chapters=10,
            completed_chapters=0,
            total_words=0,
            avg_chapter_words=0,
            completion_rate=0.0,
            last_updated=datetime(2024, 3, 15, 12, 0)
        )
        assert stats_zero.completion_rate == 0.0

        # Test with 1 completion rate
        stats_full = BookStats(
            slug="completed-book",
            title="Completed Book",
            total_chapters=10,
            completed_chapters=10,
            total_words=50000,
            avg_chapter_words=5000,
            completion_rate=1.0,
            last_updated=datetime(2024, 3, 15, 12, 0)
        )
        assert stats_full.completion_rate == 1.0

    def test_book_stats_invalid_completion_rate(self):
        """Test BookStats rejects invalid completion rates."""
        from aitext.web.models.stats_models import BookStats

        # Test with negative completion rate
        with pytest.raises(ValidationError) as exc_info:
            BookStats(
                slug="test-book",
                title="Test Book",
                total_chapters=10,
                completed_chapters=5,
                total_words=25000,
                avg_chapter_words=2500,
                completion_rate=-0.1,
                last_updated=datetime(2024, 3, 15, 12, 0)
            )
        assert "completion_rate" in str(exc_info.value)

        # Test with completion rate > 1
        with pytest.raises(ValidationError) as exc_info:
            BookStats(
                slug="test-book",
                title="Test Book",
                total_chapters=10,
                completed_chapters=5,
                total_words=25000,
                avg_chapter_words=2500,
                completion_rate=1.1,
                last_updated=datetime(2024, 3, 15, 12, 0)
            )
        assert "completion_rate" in str(exc_info.value)

    def test_book_stats_cross_field_validation(self):
        """Test BookStats cross-field validation."""
        from aitext.web.models.stats_models import BookStats

        # Test with completed_chapters > total_chapters (should fail)
        with pytest.raises(ValidationError) as exc_info:
            BookStats(
                slug="test-book",
                title="Test Book",
                total_chapters=10,
                completed_chapters=15,
                total_words=50000,
                avg_chapter_words=5000,
                completion_rate=1.0,
                last_updated=datetime(2024, 3, 15, 12, 0)
            )
        assert "completed_chapters" in str(exc_info.value)


class TestChapterStatsBasic:
    """Test ChapterStats model basic functionality."""

    def test_chapter_stats_basic(self):
        """Test ChapterStats can be created with valid data."""
        from aitext.web.models.stats_models import ChapterStats

        stats = ChapterStats(
            chapter_id=1,
            title="Chapter One",
            word_count=2500,
            character_count=16000,
            paragraph_count=25,
            has_content=True
        )

        assert stats.chapter_id == 1
        assert stats.title == "Chapter One"
        assert stats.word_count == 2500
        assert stats.character_count == 16000
        assert stats.paragraph_count == 25
        assert stats.has_content is True

    def test_chapter_stats_empty(self):
        """Test ChapterStats can represent empty chapter."""
        from aitext.web.models.stats_models import ChapterStats

        stats = ChapterStats(
            chapter_id=10,
            title="Empty Chapter",
            word_count=0,
            character_count=0,
            paragraph_count=0,
            has_content=False
        )

        assert stats.chapter_id == 10
        assert stats.word_count == 0
        assert stats.character_count == 0
        assert stats.paragraph_count == 0
        assert stats.has_content is False

    def test_chapter_stats_validation(self):
        """Test ChapterStats validates numeric constraints."""
        from aitext.web.models.stats_models import ChapterStats

        # Test with chapter_id = 0 (should fail)
        with pytest.raises(ValidationError) as exc_info:
            ChapterStats(
                chapter_id=0,
                title="Invalid Chapter",
                word_count=2500,
                character_count=16000,
                paragraph_count=25,
                has_content=True
            )
        assert "chapter_id" in str(exc_info.value)

        # Test with negative word_count (should fail)
        with pytest.raises(ValidationError) as exc_info:
            ChapterStats(
                chapter_id=1,
                title="Invalid Chapter",
                word_count=-1,
                character_count=16000,
                paragraph_count=25,
                has_content=True
            )
        assert "word_count" in str(exc_info.value)

        # Test with negative character_count (should fail)
        with pytest.raises(ValidationError) as exc_info:
            ChapterStats(
                chapter_id=1,
                title="Invalid Chapter",
                word_count=2500,
                character_count=-1,
                paragraph_count=25,
                has_content=True
            )
        assert "character_count" in str(exc_info.value)

        # Test with negative paragraph_count (should fail)
        with pytest.raises(ValidationError) as exc_info:
            ChapterStats(
                chapter_id=1,
                title="Invalid Chapter",
                word_count=2500,
                character_count=16000,
                paragraph_count=-1,
                has_content=True
            )
        assert "paragraph_count" in str(exc_info.value)

    def test_chapter_stats_cross_field_validation(self):
        """Test ChapterStats cross-field validation."""
        from aitext.web.models.stats_models import ChapterStats

        # Test with has_content=False but non-zero word_count (should fail)
        with pytest.raises(ValidationError) as exc_info:
            ChapterStats(
                chapter_id=1,
                title="Invalid Chapter",
                word_count=100,
                character_count=0,
                paragraph_count=0,
                has_content=False
            )
        assert "word_count" in str(exc_info.value)

        # Test with has_content=False but non-zero character_count (should fail)
        with pytest.raises(ValidationError) as exc_info:
            ChapterStats(
                chapter_id=1,
                title="Invalid Chapter",
                word_count=0,
                character_count=100,
                paragraph_count=0,
                has_content=False
            )
        assert "character_count" in str(exc_info.value)

        # Test with has_content=False but non-zero paragraph_count (should fail)
        with pytest.raises(ValidationError) as exc_info:
            ChapterStats(
                chapter_id=1,
                title="Invalid Chapter",
                word_count=0,
                character_count=0,
                paragraph_count=5,
                has_content=False
            )
        assert "paragraph_count" in str(exc_info.value)


class TestWritingProgressValidation:
    """Test WritingProgress model validation."""

    def test_writing_progress_basic(self):
        """Test WritingProgress can be created with valid data."""
        from aitext.web.models.stats_models import WritingProgress

        progress = WritingProgress(
            date=datetime(2024, 3, 15),
            words_written=1500,
            chapters_completed=1
        )

        assert progress.date == datetime(2024, 3, 15)
        assert progress.words_written == 1500
        assert progress.chapters_completed == 1

    def test_writing_progress_zero_values(self):
        """Test WritingProgress can have zero values."""
        from aitext.web.models.stats_models import WritingProgress

        progress = WritingProgress(
            date=datetime(2024, 3, 15),
            words_written=0,
            chapters_completed=0
        )

        assert progress.words_written == 0
        assert progress.chapters_completed == 0

    def test_writing_progress_validation(self):
        """Test WritingProgress validates numeric constraints."""
        from aitext.web.models.stats_models import WritingProgress

        # Test with negative words_written (should fail)
        with pytest.raises(ValidationError) as exc_info:
            WritingProgress(
                date=datetime(2024, 3, 15),
                words_written=-1,
                chapters_completed=0
            )
        assert "words_written" in str(exc_info.value)

        # Test with negative chapters_completed (should fail)
        with pytest.raises(ValidationError) as exc_info:
            WritingProgress(
                date=datetime(2024, 3, 15),
                words_written=1500,
                chapters_completed=-1
            )
        assert "chapters_completed" in str(exc_info.value)


class TestContentAnalysisBasic:
    """Test ContentAnalysis model basic functionality."""

    def test_content_analysis_basic(self):
        """Test ContentAnalysis can be created with valid data."""
        from aitext.web.models.stats_models import ContentAnalysis

        analysis = ContentAnalysis(
            character_mentions={
                "Alice": 15,
                "Bob": 10,
                "Charlie": 5
            },
            dialogue_ratio=0.35,
            scene_count=3,
            avg_paragraph_length=100
        )

        assert analysis.character_mentions == {"Alice": 15, "Bob": 10, "Charlie": 5}
        assert analysis.dialogue_ratio == 0.35
        assert analysis.scene_count == 3
        assert analysis.avg_paragraph_length == 100

    def test_content_analysis_minimal(self):
        """Test ContentAnalysis can be created with minimal data."""
        from aitext.web.models.stats_models import ContentAnalysis

        analysis = ContentAnalysis(
            character_mentions={},
            dialogue_ratio=0.0,
            scene_count=0,
            avg_paragraph_length=0
        )

        assert analysis.character_mentions == {}
        assert analysis.dialogue_ratio == 0.0
        assert analysis.scene_count == 0
        assert analysis.avg_paragraph_length == 0

    def test_content_analysis_validation(self):
        """Test ContentAnalysis validates numeric constraints."""
        from aitext.web.models.stats_models import ContentAnalysis

        # Test with negative dialogue_ratio (should fail)
        with pytest.raises(ValidationError) as exc_info:
            ContentAnalysis(
                character_mentions={},
                dialogue_ratio=-0.1,
                scene_count=0,
                avg_paragraph_length=0
            )
        assert "dialogue_ratio" in str(exc_info.value)

        # Test with dialogue_ratio > 1 (should fail)
        with pytest.raises(ValidationError) as exc_info:
            ContentAnalysis(
                character_mentions={},
                dialogue_ratio=1.1,
                scene_count=0,
                avg_paragraph_length=0
            )
        assert "dialogue_ratio" in str(exc_info.value)

        # Test with negative scene_count (should fail)
        with pytest.raises(ValidationError) as exc_info:
            ContentAnalysis(
                character_mentions={},
                dialogue_ratio=0.5,
                scene_count=-1,
                avg_paragraph_length=0
            )
        assert "scene_count" in str(exc_info.value)

        # Test with negative avg_paragraph_length (should fail)
        with pytest.raises(ValidationError) as exc_info:
            ContentAnalysis(
                character_mentions={},
                dialogue_ratio=0.5,
                scene_count=0,
                avg_paragraph_length=-1
            )
        assert "avg_paragraph_length" in str(exc_info.value)