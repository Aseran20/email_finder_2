"""
Pytest configuration and shared fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add backend directory to Python path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture(scope="session")
def test_domain():
    """Common test domain."""
    return "example.com"


@pytest.fixture(scope="session")
def test_full_name():
    """Common test full name."""
    return "John Doe"


@pytest.fixture
def sample_mx_records():
    """Sample MX records for testing."""
    return ["mx1.example.com", "mx2.example.com"]
