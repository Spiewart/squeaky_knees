"""Tests for input validation and sanitization."""

from config.validation import sanitize_html
from config.validation import sanitize_streamfield_blocks
from config.validation import validate_comment_length
from config.validation import validate_email
from config.validation import validate_username


class TestHtmlSanitization:
    """Test HTML sanitization for XSS prevention."""

    def test_sanitize_html_removes_script_tags(self):
        """Script tags should be removed."""
        dirty = "<p>Hello</p><script>alert('xss')</script>"
        clean = sanitize_html(dirty)
        assert "<script>" not in clean
        assert "alert" not in clean
        assert "<p>" in clean

    def test_sanitize_html_removes_event_handlers(self):
        """Event handlers should be removed."""
        dirty = "<p onclick=\"alert('xss')\">Click me</p>"
        clean = sanitize_html(dirty)
        assert "onclick" not in clean
        assert "alert" not in clean

    def test_sanitize_html_removes_iframes(self):
        """iframes should be removed."""
        dirty = '<p>Content</p><iframe src="evil.com"></iframe>'
        clean = sanitize_html(dirty)
        assert "<iframe>" not in clean
        assert "evil.com" not in clean

    def test_sanitize_html_removes_style_tags(self):
        """Style tags should be removed."""
        dirty = (
            "<style>body { background: url('javascript:alert()'); }</style><p>Text</p>"
        )
        clean = sanitize_html(dirty)
        assert "<style>" not in clean

    def test_sanitize_html_preserves_safe_content(self):
        """Safe HTML should be preserved."""
        safe = "<p>Hello <strong>world</strong></p>"
        result = sanitize_html(safe)
        assert "<p>" in result
        assert "<strong>" in result
        assert "Hello" in result

    def test_sanitize_html_handles_non_string(self):
        """Non-string input should return empty string."""
        assert sanitize_html(None) == ""
        assert sanitize_html(123) == ""
        assert sanitize_html([]) == ""


class TestCommentLengthValidation:
    """Test comment length validation."""

    def test_validate_comment_length_valid(self):
        """Valid comment length should pass."""
        blocks = [{"type": "rich_text", "value": "<p>Hello world</p>"}]
        is_valid, _error = validate_comment_length(blocks)
        assert is_valid is True
        assert _error == ""

    def test_validate_comment_length_empty(self):
        """Empty comment should fail."""
        blocks = [{"type": "rich_text", "value": "<p></p>"}]
        is_valid, _error = validate_comment_length(blocks)
        assert is_valid is False
        assert "empty" in _error.lower()

    def test_validate_comment_length_exceeds_max(self):
        """Comment exceeding max length should fail."""
        long_text = "x" * 6000
        blocks = [{"type": "rich_text", "value": f"<p>{long_text}</p>"}]
        is_valid, _error = validate_comment_length(blocks)
        assert is_valid is False
        assert "exceeds" in _error.lower()

    def test_validate_comment_length_strips_html(self):
        """HTML tags should be stripped for length calculation."""
        # 50 x's = 50 chars, wrapped in HTML tags
        blocks = [{"type": "rich_text", "value": "<p>" + "x" * 50 + "</p>"}]
        is_valid, _error = validate_comment_length(blocks)
        assert is_valid is True

    def test_validate_comment_length_code_block(self):
        """Code blocks should be included in length."""
        blocks = [
            {
                "type": "code",
                "value": {"content": "print('hello')", "language": "python"},
            },
        ]
        is_valid, _error = validate_comment_length(blocks)
        assert is_valid is True

    def test_validate_comment_length_multiple_blocks(self):
        """Multiple blocks should sum to total length."""
        blocks = [
            {"type": "rich_text", "value": "<p>" + "x" * 2000 + "</p>"},
            {"type": "code", "value": {"content": "y" * 2000, "language": "python"}},
        ]
        is_valid, _error = validate_comment_length(blocks)
        assert is_valid is True

    def test_validate_comment_length_invalid_format(self):
        """Invalid format should fail."""
        is_valid, _error = validate_comment_length("not a list")
        assert is_valid is False


class TestUsernameValidation:
    """Test username validation."""

    def test_validate_username_valid(self):
        """Valid username should pass."""
        is_valid, error = validate_username("john_doe")
        assert is_valid is True
        assert error == ""

    def test_validate_username_empty(self):
        """Empty username should fail."""
        is_valid, error = validate_username("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_username_too_short(self):
        """Username shorter than 3 chars should fail."""
        is_valid, error = validate_username("ab")
        assert is_valid is False
        assert "3 characters" in error

    def test_validate_username_too_long(self):
        """Username longer than max should fail."""
        is_valid, error = validate_username("x" * 200)
        assert is_valid is False
        assert "exceeds" in error.lower()

    def test_validate_username_invalid_chars(self):
        """Username with invalid chars should fail."""
        is_valid, error = validate_username("user@domain")
        assert is_valid is False
        assert "only contain" in error

    def test_validate_username_allows_hyphen(self):
        """Username with hyphen should pass."""
        is_valid, _error = validate_username("john-doe")
        assert is_valid is True

    def test_validate_username_allows_underscore(self):
        """Username with underscore should pass."""
        is_valid, _error = validate_username("john_doe")
        assert is_valid is True

    def test_validate_username_allows_numbers(self):
        """Username with numbers should pass."""
        is_valid, _error = validate_username("user123")
        assert is_valid is True

    def test_validate_username_non_string(self):
        """Non-string username should fail."""
        is_valid, _error = validate_username(123)
        assert is_valid is False


class TestEmailValidation:
    """Test email validation."""

    def test_validate_email_valid(self):
        """Valid email should pass."""
        is_valid, error = validate_email("user@example.com")
        assert is_valid is True
        assert error == ""

    def test_validate_email_empty(self):
        """Empty email should fail."""
        is_valid, error = validate_email("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_email_no_at_sign(self):
        """Email without @ should fail."""
        is_valid, _error = validate_email("userexample.com")
        assert is_valid is False

    def test_validate_email_no_domain_dot(self):
        """Email without domain dot should fail."""
        is_valid, _error = validate_email("user@example")
        assert is_valid is False

    def test_validate_email_multiple_at_signs(self):
        """Email with multiple @ should fail."""
        is_valid, _error = validate_email("user@domain@example.com")
        assert is_valid is False

    def test_validate_email_too_long(self):
        """Email exceeding max length should fail."""
        is_valid, error = validate_email("x" * 300 + "@example.com")
        assert is_valid is False
        assert "exceeds" in error.lower()

    def test_validate_email_local_part_too_long(self):
        """Email local part exceeding RFC 5321 should fail."""
        is_valid, _error = validate_email("x" * 100 + "@example.com")
        assert is_valid is False

    def test_validate_email_with_whitespace(self):
        """Email with whitespace should be trimmed."""
        is_valid, _error = validate_email("  user@example.com  ")
        assert is_valid is True

    def test_validate_email_uppercase(self):
        """Email should be lowercased."""
        is_valid, _error = validate_email("USER@EXAMPLE.COM")
        assert is_valid is True

    def test_validate_email_non_string(self):
        """Non-string email should fail."""
        is_valid, _error = validate_email(123)
        assert is_valid is False


class TestStreamFieldSanitization:
    """Test StreamField block sanitization."""

    def test_sanitize_streamfield_blocks_valid(self):
        """Valid blocks should pass through sanitized."""
        blocks = [
            {"type": "rich_text", "value": "<p>Hello</p>"},
            {
                "type": "code",
                "value": {"content": "print('test')", "language": "python"},
            },
        ]
        sanitized, errors = sanitize_streamfield_blocks(blocks)
        assert len(sanitized) == 2
        assert len(errors) == 0

    def test_sanitize_streamfield_blocks_removes_xss(self):
        """XSS attempts should be removed."""
        blocks = [
            {"type": "rich_text", "value": "<p>Hello<script>alert('xss')</script></p>"},
        ]
        sanitized, errors = sanitize_streamfield_blocks(blocks)
        assert len(sanitized) == 1
        assert "<script>" not in sanitized[0]["value"]
        assert len(errors) == 0

    def test_sanitize_streamfield_blocks_invalid_rich_text_value(self):
        """Rich text with non-string value should error."""
        blocks = [
            {"type": "rich_text", "value": 123},
        ]
        sanitized, errors = sanitize_streamfield_blocks(blocks)
        assert len(sanitized) == 0
        assert len(errors) == 1

    def test_sanitize_streamfield_blocks_code_too_long(self):
        """Code block exceeding max length should error."""
        blocks = [
            {"type": "code", "value": {"content": "x" * 15000, "language": "python"}},
        ]
        sanitized, errors = sanitize_streamfield_blocks(blocks)
        assert len(sanitized) == 0
        assert len(errors) == 1
        assert "exceeds" in errors[0]

    def test_sanitize_streamfield_blocks_invalid_type(self):
        """Block with non-dict should error."""
        blocks = ["not a dict"]
        sanitized, errors = sanitize_streamfield_blocks(blocks)
        assert len(sanitized) == 0
        assert len(errors) == 1

    def test_sanitize_streamfield_blocks_unknown_type(self):
        """Block with unknown type should error."""
        blocks = [
            {"type": "unknown", "value": "something"},
        ]
        sanitized, errors = sanitize_streamfield_blocks(blocks)
        assert len(sanitized) == 0
        assert len(errors) == 1
        assert "unknown type" in errors[0]

    def test_sanitize_streamfield_blocks_code_without_language(self):
        """Code block without language should work."""
        blocks = [
            {"type": "code", "value": {"content": "print('test')"}},
        ]
        sanitized, _errors = sanitize_streamfield_blocks(blocks)
        assert len(sanitized) == 1
        assert sanitized[0]["value"]["language"] == ""
