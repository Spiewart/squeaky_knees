import json

import pytest

from squeaky_knees.blog.forms import CommentForm


@pytest.mark.django_db
class TestCommentForm:
    """Tests for comment form."""

    def test_comment_form_valid_data(self):
        """Test comment form with valid plain text data including captcha."""
        form = CommentForm(
            data={
                "text": "This is a test comment",
                "captcha": "test_token",
            },
        )
        assert "text" in form.fields
        assert form.is_valid()
        cleaned = form.cleaned_data["text"]
        assert cleaned[0]["type"] == "rich_text"

    def test_comment_form_empty_text(self):
        """Test comment form with empty text."""
        form = CommentForm(data={"text": ""})
        assert not form.is_valid()
        assert "text" in form.errors

    def test_comment_form_has_form_helper(self):
        """Test comment form has crispy forms helper."""
        form = CommentForm()
        assert hasattr(form, "helper")
        assert form.helper.form_tag is False

    def test_comment_form_renders_correctly(self):
        """Test comment form renders with correct widgets."""
        form = CommentForm()
        assert "text" in form.fields
        assert form.fields["text"].label == "Your Comment"

    def test_comment_form_has_captcha_field(self):
        """Test comment form includes reCAPTCHA field."""
        form = CommentForm()
        assert "captcha" in form.fields

    def test_comment_form_accepts_json_payload(self):
        """Test comment form accepts JSON StreamField payloads."""
        payload = json.dumps(
            [
                {"type": "rich_text", "value": "<p>Hello</p>"},
                {
                    "type": "code",
                    "value": {"language": "python", "code": "print('ok')"},
                },
            ],
        )
        form = CommentForm(data={"text": payload})
        assert form.is_valid()
        cleaned = form.cleaned_data["text"]
        assert cleaned[1]["type"] == "code"

    def test_comment_form_rejects_empty_json_payload(self):
        """Test comment form rejects empty JSON payloads."""
        form = CommentForm(data={"text": json.dumps([])})
        assert not form.is_valid()
        assert "text" in form.errors

    def test_comment_form_falls_back_on_invalid_json(self):
        """Test invalid JSON falls back to plain text wrapping."""
        form = CommentForm(data={"text": "{invalid json"})
        assert form.is_valid()
        cleaned = form.cleaned_data["text"]
        assert cleaned[0]["type"] == "rich_text"
