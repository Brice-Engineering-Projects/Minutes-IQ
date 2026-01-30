"""Unit tests for authorization code generation and validation."""

import re

from minutes_iq.db.auth_code_service import AuthCodeService


class TestCodeGeneration:
    """Test code generation logic."""

    def test_generate_code_format(self):
        """Test that generated codes follow the correct format."""
        code = AuthCodeService.generate_code()

        # Should be in format XXXX-XXXX-XXXX
        assert len(code) == 14  # 12 chars + 2 hyphens
        assert code[4] == "-"
        assert code[9] == "-"

        # Should only contain uppercase letters and digits
        code_without_hyphens = code.replace("-", "")
        assert code_without_hyphens.isupper()
        assert code_without_hyphens.isalnum()

    def test_generate_code_is_random(self):
        """Test that generated codes are not predictable."""
        codes = [AuthCodeService.generate_code() for _ in range(100)]

        # All codes should be unique
        assert len(set(codes)) == 100

    def test_generate_code_character_set(self):
        """Test that codes only use allowed characters."""
        allowed_pattern = re.compile(r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")

        for _ in range(50):
            code = AuthCodeService.generate_code()
            assert allowed_pattern.match(code), f"Code {code} doesn't match pattern"

    def test_generate_code_length(self):
        """Test that codes are exactly 12 characters (without hyphens)."""
        code = AuthCodeService.generate_code()
        code_without_hyphens = code.replace("-", "")
        assert len(code_without_hyphens) == 12


class TestCodeNormalization:
    """Test code normalization logic."""

    def test_normalize_removes_hyphens(self):
        """Test that normalization removes hyphens."""
        code = "ABCD-EFGH-IJKL"
        normalized = AuthCodeService.normalize_code(code)
        assert normalized == "ABCDEFGHIJKL"

    def test_normalize_removes_spaces(self):
        """Test that normalization removes spaces."""
        code = "ABCD EFGH IJKL"
        normalized = AuthCodeService.normalize_code(code)
        assert normalized == "ABCDEFGHIJKL"

    def test_normalize_converts_to_uppercase(self):
        """Test that normalization converts to uppercase."""
        code = "abcd-efgh-ijkl"
        normalized = AuthCodeService.normalize_code(code)
        assert normalized == "ABCDEFGHIJKL"

    def test_normalize_mixed_case_and_formatting(self):
        """Test normalization with mixed case and formatting."""
        code = "AbCd-eFgH ijKl"
        normalized = AuthCodeService.normalize_code(code)
        assert normalized == "ABCDEFGHIJKL"

    def test_normalize_already_normalized(self):
        """Test that normalizing an already normalized code doesn't change it."""
        code = "ABCDEFGHIJKL"
        normalized = AuthCodeService.normalize_code(code)
        assert normalized == code
