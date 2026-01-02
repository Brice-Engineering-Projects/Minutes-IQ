"""Unit tests for password hashing functionality."""

from jea_meeting_web_scraper.auth.security import get_password_hash, verify_password


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_different_hash_each_time(self):
        """Test that hashing the same password twice produces different hashes."""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert hash1 != password
        assert hash2 != password

    def test_verify_password_with_correct_password(self):
        """Test that password verification succeeds with correct password."""
        password = "my_secure_password"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_with_incorrect_password(self):
        """Test that password verification fails with incorrect password."""
        password = "correct_password"
        hashed = get_password_hash(password)

        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "MyPassword"
        hashed = get_password_hash(password)

        assert verify_password("mypassword", hashed) is False
        assert verify_password("MYPASSWORD", hashed) is False

    def test_hash_empty_password(self):
        """Test hashing an empty password."""
        password = ""
        hashed = get_password_hash(password)

        assert hashed != ""
        assert verify_password(password, hashed) is True

    def test_hash_special_characters(self):
        """Test hashing passwords with special characters."""
        password = "p@ssw0rd!#$%^&*()"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_hash_unicode_password(self):
        """Test hashing passwords with unicode characters."""
        password = "пароль密码🔐"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
