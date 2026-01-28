"""
Integration tests for FastAPI endpoints.
Tests API endpoints with mocked EmailFinder to avoid real SMTP calls.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from main import app
from models import EmailFinderResponse


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_valid_response():
    """Mock response for valid email."""
    return EmailFinderResponse(
        status="valid",
        email="john.doe@example.com",
        patternsTested=["john.doe@example.com", "johndoe@example.com"],
        smtpLogs=["mx.example.com: 250 OK"],
        catchAll=False,
        mxRecords=["mx.example.com"],
        debugInfo="MX: mx.example.com | Match: john.doe@example.com",
        errorMessage=None
    )


@pytest.fixture
def mock_catch_all_response():
    """Mock response for catch-all server."""
    return EmailFinderResponse(
        status="catch_all",
        email="john.doe@example.com",
        patternsTested=["john.doe@example.com"],
        smtpLogs=["mx.example.com: 250 OK (random accepted)"],
        catchAll=True,
        mxRecords=["mx.example.com"],
        debugInfo="MX: mx.example.com | Catch-all detected",
        errorMessage=None
    )


class TestFindEmailEndpoint:
    """Test /api/find-email endpoint."""

    @patch('main.finder.find_email')
    def test_find_email_success(self, mock_find, client, mock_valid_response):
        """Test successful email finding."""
        mock_find.return_value = mock_valid_response

        response = client.post(
            "/api/find-email",
            json={"domain": "example.com", "fullName": "John Doe"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "valid"
        assert data["email"] == "john.doe@example.com"
        assert data["catchAll"] is False

    @patch('main.finder.find_email')
    def test_find_email_catch_all(self, mock_find, client, mock_catch_all_response):
        """Test catch-all detection."""
        mock_find.return_value = mock_catch_all_response

        response = client.post(
            "/api/find-email",
            json={"domain": "example.com", "fullName": "John Doe"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "catch_all"
        assert data["catchAll"] is True

    def test_find_email_missing_domain(self, client):
        """Test validation - missing domain."""
        response = client.post(
            "/api/find-email",
            json={"fullName": "John Doe"}
        )

        assert response.status_code == 422  # Validation error

    def test_find_email_missing_fullname(self, client):
        """Test validation - missing fullName."""
        response = client.post(
            "/api/find-email",
            json={"domain": "example.com"}
        )

        assert response.status_code == 422  # Validation error

    def test_find_email_empty_values(self, client):
        """Test validation - empty strings."""
        response = client.post(
            "/api/find-email",
            json={"domain": "", "fullName": ""}
        )

        # Should return 400 because of custom validation in endpoint
        assert response.status_code == 400

    @patch('main.finder.find_email')
    def test_find_email_exception_handling(self, mock_find, client):
        """Test exception handling in endpoint."""
        mock_find.side_effect = Exception("SMTP connection failed")

        response = client.post(
            "/api/find-email",
            json={"domain": "example.com", "fullName": "John Doe"}
        )

        assert response.status_code == 200  # Returns 200 with error status
        data = response.json()
        assert data["status"] == "error"
        assert "SMTP connection failed" in data["errorMessage"]


class TestHistoryEndpoint:
    """Test /api/history endpoint."""

    @patch('main.get_db')
    def test_get_history_success(self, mock_get_db, client):
        """Test retrieving history."""
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_get_db.return_value = mock_db

        response = client.get("/api/history?limit=10")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch('main.get_db')
    def test_get_history_default_limit(self, mock_get_db, client):
        """Test default limit of 50."""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_get_db.return_value = mock_db

        response = client.get("/api/history")

        assert response.status_code == 200
        # Verify limit was called with 50 (default)
        mock_query.limit.assert_called_once_with(50)


class TestBulkSearchEndpoint:
    """Test /api/bulk-search endpoint."""

    def test_bulk_search_csv_missing_file(self, client):
        """Test bulk search without file."""
        response = client.post("/api/bulk-search")

        assert response.status_code == 422  # Missing required file

    @patch('main.finder.find_email')
    def test_bulk_search_csv_success(self, mock_find, client, mock_valid_response):
        """Test bulk search with valid CSV."""
        mock_find.return_value = mock_valid_response

        csv_content = b"domain,fullName\nexample.com,John Doe"
        files = {"file": ("test.csv", csv_content, "text/csv")}

        response = client.post("/api/bulk-search", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "results" in data
        assert data["total"] >= 1

    def test_bulk_search_invalid_file_type(self, client):
        """Test bulk search with invalid file type."""
        files = {"file": ("test.txt", b"invalid content", "text/plain")}

        response = client.post("/api/bulk-search", files=files)

        assert response.status_code == 400
        assert "must be CSV or Excel" in response.json()["detail"]

    @patch('main.finder.find_email')
    def test_bulk_search_missing_columns(self, mock_find, client):
        """Test bulk search with missing required columns."""
        csv_content = b"name,email\nJohn,john@example.com"
        files = {"file": ("test.csv", csv_content, "text/csv")}

        response = client.post("/api/bulk-search", files=files)

        assert response.status_code == 400
        assert "domain" in response.json()["detail"].lower()

    @patch('main.finder.find_email')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_bulk_search_rate_limiting(self, mock_sleep, mock_find, client, mock_valid_response):
        """Test that rate limiting (sleep) is applied."""
        mock_find.return_value = mock_valid_response

        csv_content = b"domain,fullName\nexample.com,John Doe\nexample.com,Jane Smith"
        files = {"file": ("test.csv", csv_content, "text/csv")}

        response = client.post("/api/bulk-search", files=files)

        assert response.status_code == 200
        # Sleep should be called between requests
        assert mock_sleep.call_count >= 1
        mock_sleep.assert_called_with(1)

    @patch('main.finder.find_email')
    @patch('time.sleep')
    def test_bulk_search_consecutive_errors_stop(self, mock_sleep, mock_find, client):
        """Test that processing stops after too many consecutive errors."""
        mock_find.side_effect = Exception("Connection failed")

        # Create CSV with 10 entries
        csv_lines = ["domain,fullName"] + [f"example.com,Person {i}" for i in range(10)]
        csv_content = "\n".join(csv_lines).encode()
        files = {"file": ("test.csv", csv_content, "text/csv")}

        response = client.post("/api/bulk-search", files=files)

        assert response.status_code == 200
        data = response.json()

        # Should stop after MAX_CONSECUTIVE_ERRORS (5)
        # Total results = 5 errors + 1 STOPPED message
        assert data["total"] <= 6
        # Check for stop message
        assert any("STOPPED" in str(r) for r in data["results"])


class TestOpenAPISpec:
    """Test OpenAPI documentation generation."""

    def test_openapi_accessible(self, client):
        """Test that OpenAPI spec is accessible."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        spec = response.json()
        assert "openapi" in spec
        assert "paths" in spec

    def test_docs_accessible(self, client):
        """Test that Swagger docs are accessible."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert b"swagger" in response.content.lower()
