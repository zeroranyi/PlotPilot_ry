"""Tests for unified error handling middleware."""
import pytest
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, ValidationError

from interfaces.api.middleware.error_handler import add_error_handlers
from interfaces.api.responses import ErrorResponse


class SampleRequest(BaseModel):
    """Sample request model for testing validation."""
    name: str = Field(..., min_length=1)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@pytest.fixture
def test_app():
    """Create a test FastAPI app with error handlers."""
    # Create app without default error middleware
    app = FastAPI()

    @app.get("/success")
    async def success_endpoint():
        return {"message": "success"}

    @app.get("/not-found")
    async def not_found_endpoint():
        raise HTTPException(status_code=404, detail="Resource not found")

    @app.get("/unauthorized")
    async def unauthorized_endpoint():
        raise HTTPException(status_code=401, detail="Unauthorized access")

    @app.get("/forbidden")
    async def forbidden_endpoint():
        raise HTTPException(status_code=403, detail="Forbidden access")

    @app.get("/bad-request")
    async def bad_request_endpoint():
        raise HTTPException(status_code=400, detail="Bad request")

    @app.get("/conflict")
    async def conflict_endpoint():
        raise HTTPException(status_code=409, detail="Resource conflict")

    @app.post("/validate")
    async def validate_endpoint(data: SampleRequest):
        return {"name": data.name, "email": data.email}

    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Something went wrong")

    @app.get("/exception")
    async def exception_endpoint():
        raise Exception("Generic exception")

    # Add error handlers BEFORE other middleware
    add_error_handlers(app)

    return app


class TestHTTPExceptionHandler:
    """Tests for HTTP exception handler."""

    def test_http_exception_handler_404(self, test_app):
        """Test HTTP 404 errors are handled with NOT_FOUND code."""
        client = TestClient(test_app)
        response = client.get("/not-found")

        assert response.status_code == 404
        data = response.json()

        assert data["success"] is False
        assert data["code"] == "NOT_FOUND"
        assert "Resource not found" in data["message"]

    def test_http_exception_handler_401(self, test_app):
        """Test HTTP 401 errors are handled with UNAUTHORIZED code."""
        client = TestClient(test_app)
        response = client.get("/unauthorized")

        assert response.status_code == 401
        data = response.json()

        assert data["success"] is False
        assert data["code"] == "UNAUTHORIZED"
        assert "Unauthorized access" in data["message"]

    def test_http_exception_handler_403(self, test_app):
        """Test HTTP 403 errors are handled with FORBIDDEN code."""
        client = TestClient(test_app)
        response = client.get("/forbidden")

        assert response.status_code == 403
        data = response.json()

        assert data["success"] is False
        assert data["code"] == "FORBIDDEN"
        assert "Forbidden access" in data["message"]

    def test_http_exception_handler_400(self, test_app):
        """Test HTTP 400 errors are handled with BAD_REQUEST code."""
        client = TestClient(test_app)
        response = client.get("/bad-request")

        assert response.status_code == 400
        data = response.json()

        assert data["success"] is False
        assert data["code"] == "BAD_REQUEST"
        assert "Bad request" in data["message"]

    def test_http_exception_handler_409(self, test_app):
        """Test HTTP 409 errors are handled with CONFLICT code."""
        client = TestClient(test_app)
        response = client.get("/conflict")

        assert response.status_code == 409
        data = response.json()

        assert data["success"] is False
        assert data["code"] == "CONFLICT"
        assert "Resource conflict" in data["message"]

    def test_http_exception_handler_default_code(self, test_app):
        """Test HTTP exceptions with unmapped status codes use default code."""
        client = TestClient(test_app)

        # Make request to endpoint that raises HTTPException with unmapped code
        # We'll test this by creating a new endpoint on the fly
        from fastapi import APIRouter
        router = APIRouter()

        @router.get("/custom-418")
        async def custom_endpoint():
            raise HTTPException(status_code=418, detail="I'm a teapot")

        test_app.include_router(router)
        response = client.get("/custom-418")

        assert response.status_code == 418
        data = response.json()

        assert data["success"] is False
        # Should use a generic code for unmapped status
        assert data["code"] == "HTTP_ERROR"
        assert "I'm a teapot" in data["message"]


class TestValidationErrorHandler:
    """Tests for validation error handler."""

    def test_validation_error_handler_missing_required_field(self, test_app):
        """Test 422 validation errors for missing required fields."""
        client = TestClient(test_app)

        response = client.post("/validate", json={})
        assert response.status_code == 422

        data = response.json()
        assert data["success"] is False
        assert data["code"] == "UNPROCESSABLE_ENTITY"
        assert "details" in data

        # Check that details contain field errors
        assert isinstance(data["details"], list)
        assert len(data["details"]) > 0

        # Check structure of first error
        first_error = data["details"][0]
        assert "field" in first_error
        assert "message" in first_error
        assert "type" in first_error

    def test_validation_error_handler_invalid_email_format(self, test_app):
        """Test 422 validation errors for invalid field formats."""
        client = TestClient(test_app)

        response = client.post("/validate", json={
            "name": "Test User",
            "email": "invalid-email"
        })
        assert response.status_code == 422

        data = response.json()
        assert data["success"] is False
        assert data["code"] == "UNPROCESSABLE_ENTITY"
        assert "details" in data

        # Check that email field has validation error
        email_errors = [e for e in data["details"] if "email" in str(e.get("field", ""))]
        assert len(email_errors) > 0

    def test_validation_error_handler_too_short_string(self, test_app):
        """Test 422 validation errors for string length validation."""
        client = TestClient(test_app)

        response = client.post("/validate", json={
            "name": "",  # Too short (min_length=1)
            "email": "test@example.com"
        })
        assert response.status_code == 422

        data = response.json()
        assert data["success"] is False
        assert data["code"] == "UNPROCESSABLE_ENTITY"
        assert "details" in data

        # Check that name field has validation error
        name_errors = [e for e in data["details"] if "name" in str(e.get("field", ""))]
        assert len(name_errors) > 0

    def test_validation_error_handler_multiple_fields(self, test_app):
        """Test 422 validation errors when multiple fields fail."""
        client = TestClient(test_app)

        response = client.post("/validate", json={
            "name": "",  # Too short
            "email": "invalid"  # Invalid format
        })
        assert response.status_code == 422

        data = response.json()
        assert data["success"] is False
        assert data["code"] == "UNPROCESSABLE_ENTITY"
        assert "details" in data

        # Should have multiple errors
        assert len(data["details"]) >= 2


class TestGenericExceptionHandler:
    """Tests for generic exception handler."""

    def test_generic_exception_handler_value_error(self, test_app):
        """Test 500 errors for ValueError exceptions."""
        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/error")

        assert response.status_code == 500
        data = response.json()

        assert data["success"] is False
        assert data["code"] == "INTERNAL_ERROR"
        assert "Something went wrong" in data["message"]

    def test_generic_exception_handler_generic_exception(self, test_app):
        """Test 500 errors for generic exceptions."""
        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/exception")

        assert response.status_code == 500
        data = response.json()

        assert data["success"] is False
        assert data["code"] == "INTERNAL_ERROR"
        assert "Generic exception" in data["message"]

    def test_generic_exception_handler_runtime_error(self, test_app):
        """Test 500 errors for RuntimeError exceptions."""
        # Add endpoint that raises RuntimeError
        from fastapi import APIRouter
        router = APIRouter()

        @router.get("/runtime-error")
        async def runtime_error_endpoint():
            raise RuntimeError("Runtime error occurred")

        test_app.include_router(router)
        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/runtime-error")

        assert response.status_code == 500
        data = response.json()

        assert data["success"] is False
        assert data["code"] == "INTERNAL_ERROR"
        assert "Runtime error occurred" in data["message"]


class TestSuccessResponseFormat:
    """Tests to ensure successful responses still work correctly."""

    def test_success_response_unaffected(self, test_app):
        """Test that successful responses are not affected by error handlers."""
        client = TestClient(test_app)
        response = client.get("/success")

        assert response.status_code == 200
        data = response.json()

        # Should return raw data, not wrapped in SuccessResponse
        # (unless endpoints are updated to use SuccessResponse)
        assert data["message"] == "success"

    def test_valid_request_returns_200(self, test_app):
        """Test that valid POST requests work correctly."""
        client = TestClient(test_app)

        response = client.post("/validate", json={
            "name": "Test User",
            "email": "test@example.com"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"
