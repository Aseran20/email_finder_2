"""
Unit tests for EmailFinder core logic.
Tests pattern generation, name normalization, and email verification.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from core.email_finder import EmailFinder
from models import EmailFinderResponse


class TestNormalization:
    """Test name and domain normalization."""

    def setup_method(self):
        self.finder = EmailFinder()

    def test_normalize_domain_basic(self):
        """Test basic domain normalization."""
        assert self.finder.normalize_domain("example.com") == "example.com"
        assert self.finder.normalize_domain("EXAMPLE.COM") == "example.com"
        assert self.finder.normalize_domain("  example.com  ") == "example.com"

    def test_normalize_domain_with_protocol(self):
        """Test domain normalization with URLs."""
        assert self.finder.normalize_domain("https://example.com") == "example.com"
        assert self.finder.normalize_domain("http://example.com/path") == "example.com"

    def test_normalize_name_simple(self):
        """Test simple name normalization."""
        first_variants, last_variants = self.finder.normalize_name("John Doe")
        assert "john" in first_variants
        assert "doe" in last_variants

    def test_normalize_name_with_accents(self):
        """Test name with accents (André Müller)."""
        first_variants, last_variants = self.finder.normalize_name("André Müller")
        assert "andre" in first_variants
        assert "muller" in last_variants

    def test_normalize_name_with_hyphens(self):
        """Test hyphenated names (Mads-Håkon Mørck)."""
        first_variants, last_variants = self.finder.normalize_name("Mads-Håkon Mørck")
        # Should have both hyphenated and non-hyphenated versions
        assert any("mads" in v for v in first_variants)
        assert "morck" in last_variants

    def test_normalize_name_single_word(self):
        """Test single name (Madonna)."""
        first_variants, last_variants = self.finder.normalize_name("Madonna")
        assert "madonna" in first_variants
        assert last_variants == [""]

    def test_normalize_name_edge_cases(self):
        """Test edge cases in name normalization."""
        # Empty string
        first_variants, last_variants = self.finder.normalize_name("")
        assert first_variants == [""]

        # Special characters
        first_variants, last_variants = self.finder.normalize_name("Jean-François D'Arcy")
        assert any("jean" in v for v in first_variants)
        assert "darcy" in last_variants


class TestPatternGeneration:
    """Test email pattern generation."""

    def setup_method(self):
        self.finder = EmailFinder()

    def test_generate_patterns_basic(self):
        """Test basic pattern generation."""
        patterns = self.finder.generate_patterns(["john"], ["doe"], "example.com")

        # Check key patterns are present
        assert "john.doe@example.com" in patterns
        assert "johndoe@example.com" in patterns
        assert "j.doe@example.com" in patterns
        assert "john.d@example.com" in patterns
        assert "john@example.com" in patterns
        assert "doe@example.com" in patterns

    def test_generate_patterns_extended(self):
        """Test extended patterns (missing permutations)."""
        patterns = self.finder.generate_patterns(["john"], ["doe"], "example.com")

        # Check new patterns from Edge Case #2
        assert "jdoe@example.com" in patterns
        assert "doej@example.com" in patterns
        assert "johnd@example.com" in patterns

    def test_generate_patterns_hyphenated(self):
        """Test patterns with hyphenated names."""
        patterns = self.finder.generate_patterns(
            ["mads-hakon", "madshakon"],
            ["morck"],
            "example.com"
        )

        # Should have patterns for both variants
        assert "mads-hakon.morck@example.com" in patterns
        assert "madshakon.morck@example.com" in patterns

    def test_generate_patterns_no_duplicates(self):
        """Test that patterns don't contain duplicates."""
        patterns = self.finder.generate_patterns(["john"], ["doe"], "example.com")
        assert len(patterns) == len(set(patterns)), "Patterns contain duplicates"

    def test_generate_patterns_order(self):
        """Test that most common patterns come first."""
        patterns = self.finder.generate_patterns(["john"], ["doe"], "example.com")

        # first.last@ should be first (most common)
        assert patterns[0] == "john.doe@example.com"


class TestEmailVerification:
    """Test SMTP verification logic (mocked)."""

    def setup_method(self):
        self.finder = EmailFinder()

    @patch('smtplib.SMTP')
    def test_verify_email_valid(self, mock_smtp):
        """Test verification of valid email."""
        # Mock SMTP responses
        mock_server = MagicMock()
        mock_server.rcpt.return_value = (250, b"2.1.5 Recipient OK")
        mock_smtp.return_value = mock_server

        is_valid, log, code = self.finder.verify_email("test@example.com", "mx.example.com")

        assert is_valid is True
        assert code == 250
        assert "mx.example.com" in log

    @patch('smtplib.SMTP')
    def test_verify_email_invalid(self, mock_smtp):
        """Test verification of invalid email."""
        mock_server = MagicMock()
        mock_server.rcpt.return_value = (550, b"5.1.1 User unknown")
        mock_smtp.return_value = mock_server

        is_valid, log, code = self.finder.verify_email("fake@example.com", "mx.example.com")

        assert is_valid is False
        assert code == 550

    @patch('smtplib.SMTP')
    def test_verify_email_timeout(self, mock_smtp):
        """Test timeout handling."""
        mock_server = MagicMock()
        mock_server.connect.side_effect = TimeoutError()
        mock_smtp.return_value = mock_server

        is_valid, log, code = self.finder.verify_email("test@example.com", "mx.example.com")

        assert is_valid is False
        assert "Timeout" in log
        assert code == 0

    @patch('smtplib.SMTP')
    def test_verify_email_connection_refused(self, mock_smtp):
        """Test connection refused handling."""
        mock_server = MagicMock()
        mock_server.connect.side_effect = ConnectionRefusedError()
        mock_smtp.return_value = mock_server

        is_valid, log, code = self.finder.verify_email("test@example.com", "mx.example.com")

        assert is_valid is False
        assert "refused" in log.lower()


class TestCatchAllDetection:
    """Test catch-all server detection."""

    def setup_method(self):
        self.finder = EmailFinder()

    @patch.object(EmailFinder, 'get_mx_records')
    @patch.object(EmailFinder, 'verify_email')
    def test_detect_catch_all(self, mock_verify, mock_mx):
        """Test catch-all detection."""
        # Setup mocks
        mock_mx.return_value = ["mx.example.com"]

        # First call (random email) returns valid -> catch-all
        mock_verify.side_effect = [
            (True, "250 OK", 250),  # Random email accepted = catch-all
        ]

        result = self.finder.find_email("example.com", "John Doe")

        assert result.status == "catch_all"
        assert result.catchAll is True
        assert result.email is not None  # Should return best guess

    @patch.object(EmailFinder, 'get_mx_records')
    @patch.object(EmailFinder, 'verify_email')
    def test_honest_server_finds_email(self, mock_verify, mock_mx):
        """Test honest server finding real email."""
        # Setup mocks
        mock_mx.return_value = ["mx.example.com"]

        # Catch-all check fails, then first pattern succeeds
        mock_verify.side_effect = [
            (False, "550 Not found", 550),  # Random email rejected (honest server)
            (True, "250 OK", 250),          # First pattern accepted
        ]

        result = self.finder.find_email("example.com", "John Doe")

        assert result.status == "valid"
        assert result.catchAll is False
        assert result.email == "john.doe@example.com"

    @patch.object(EmailFinder, 'get_mx_records')
    @patch.object(EmailFinder, 'verify_email')
    def test_no_match_found(self, mock_verify, mock_mx):
        """Test when no pattern matches."""
        # Setup mocks
        mock_mx.return_value = ["mx.example.com"]

        # All emails rejected
        mock_verify.return_value = (False, "550 Not found", 550)

        result = self.finder.find_email("example.com", "John Doe")

        assert result.status == "not_found"
        assert result.email is None

    @patch.object(EmailFinder, 'get_mx_records')
    def test_no_mx_records(self, mock_mx):
        """Test domain with no MX records."""
        mock_mx.return_value = []

        result = self.finder.find_email("invalid-domain.com", "John Doe")

        assert result.status == "error"
        assert "No MX records" in result.errorMessage


class TestIntegration:
    """Integration tests with real logic but mocked network."""

    def setup_method(self):
        self.finder = EmailFinder()

    @patch('dns.resolver.resolve')
    @patch('smtplib.SMTP')
    def test_full_workflow_adrian_turion(self, mock_smtp, mock_dns):
        """Test the full workflow with Adrian Turion @ auraia.ch."""
        # Mock DNS
        mock_mx_record = Mock()
        mock_mx_record.preference = 10
        mock_mx_record.exchange = "auraia-ch.mail.protection.outlook.com."
        mock_dns.return_value = [mock_mx_record]

        # Mock SMTP
        mock_server = MagicMock()
        # Random email rejected (honest server), first pattern accepted
        mock_server.rcpt.side_effect = [
            (550, b"Access denied"),
            (250, b"Recipient OK"),
        ]
        mock_smtp.return_value = mock_server

        result = self.finder.find_email("auraia.ch", "Adrian Turion")

        assert result.status == "valid"
        assert result.email == "adrian.turion@auraia.ch"
        assert result.catchAll is False
        assert "auraia-ch.mail.protection.outlook.com" in result.mxRecords[0]
