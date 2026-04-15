"""Tests for unified response models."""
import pytest
from typing import List
from pydantic import ValidationError

from web.models.responses import SuccessResponse, ErrorResponse, PaginatedResponse


class TestSuccessResponse:
    """Tests for SuccessResponse model."""

    def test_success_response_basic(self):
        """Test basic success response with data."""
        response = SuccessResponse(data={"id": 1, "name": "test"})

        assert response.success is True
        assert response.data == {"id": 1, "name": "test"}
        assert response.message is None

        # Test serialization
        response_dict = response.model_dump()
        assert response_dict["success"] is True
        assert response_dict["data"] == {"id": 1, "name": "test"}

    def test_success_response_with_message(self):
        """Test success response with custom message."""
        response = SuccessResponse(
            data={"id": 1, "name": "test"},
            message="Operation completed successfully"
        )

        assert response.success is True
        assert response.data == {"id": 1, "name": "test"}
        assert response.message == "Operation completed successfully"

        # Test serialization
        response_dict = response.model_dump()
        assert response_dict["message"] == "Operation completed successfully"

    def test_success_response_with_list_data(self):
        """Test success response with list data."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = SuccessResponse(data=data)

        assert response.success is True
        assert response.data == data
        assert len(response.data) == 3

    def test_success_response_with_none_data(self):
        """Test success response with None data."""
        response = SuccessResponse(data=None)

        assert response.success is True
        assert response.data is None


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_error_response_basic(self):
        """Test basic error response."""
        response = ErrorResponse(
            message="An error occurred",
            code="ERROR_001"
        )

        assert response.success is False
        assert response.message == "An error occurred"
        assert response.code == "ERROR_001"
        assert response.details is None

        # Test serialization
        response_dict = response.model_dump()
        assert response_dict["success"] is False
        assert response_dict["message"] == "An error occurred"
        assert response_dict["code"] == "ERROR_001"

    def test_error_response_with_details(self):
        """Test error response with additional details."""
        details = {
            "field": "email",
            "reason": "Invalid format",
            "example": "user@example.com"
        }
        response = ErrorResponse(
            message="Validation failed",
            code="VALIDATION_ERROR",
            details=details
        )

        assert response.success is False
        assert response.message == "Validation failed"
        assert response.code == "VALIDATION_ERROR"
        assert response.details == details
        assert response.details["field"] == "email"

    def test_error_response_required_fields(self):
        """Test that message and code are required."""
        with pytest.raises(ValidationError):
            ErrorResponse()

        with pytest.raises(ValidationError):
            ErrorResponse(message="Error")

        with pytest.raises(ValidationError):
            ErrorResponse(code="ERROR_001")


class TestPaginatedResponse:
    """Tests for PaginatedResponse model."""

    def test_paginated_response(self):
        """Test basic paginated response."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = PaginatedResponse(
            data=data,
            total=100,
            page=1,
            page_size=10
        )

        assert response.success is True
        assert response.data == data
        assert response.total == 100
        assert response.page == 1
        assert response.page_size == 10
        assert response.total_pages == 10  # 100 / 10

        # Test serialization
        response_dict = response.model_dump()
        assert response_dict["success"] is True
        assert response_dict["total"] == 100
        assert response_dict["total_pages"] == 10

    def test_paginated_response_validation(self):
        """Test paginated response validation."""
        # Test with invalid page (must be >= 1)
        with pytest.raises(ValidationError):
            PaginatedResponse(
                data=[],
                total=100,
                page=0,
                page_size=10
            )

        # Test with invalid page_size (must be >= 1)
        with pytest.raises(ValidationError):
            PaginatedResponse(
                data=[],
                total=100,
                page=1,
                page_size=0
            )

        # Test with negative total
        with pytest.raises(ValidationError):
            PaginatedResponse(
                data=[],
                total=-1,
                page=1,
                page_size=10
            )

    def test_paginated_response_total_pages_calculation(self):
        """Test total_pages calculation with various scenarios."""
        # Exact division
        response = PaginatedResponse(data=[], total=100, page=1, page_size=10)
        assert response.total_pages == 10

        # With remainder (should round up)
        response = PaginatedResponse(data=[], total=95, page=1, page_size=10)
        assert response.total_pages == 10

        # Less than one page
        response = PaginatedResponse(data=[], total=5, page=1, page_size=10)
        assert response.total_pages == 1

        # Empty result
        response = PaginatedResponse(data=[], total=0, page=1, page_size=10)
        assert response.total_pages == 0

    def test_paginated_response_with_message(self):
        """Test paginated response with custom message."""
        response = PaginatedResponse(
            data=[{"id": 1}],
            total=1,
            page=1,
            page_size=10,
            message="Results retrieved successfully"
        )

        assert response.message == "Results retrieved successfully"
        assert response.total_pages == 1
