import pytest

from squeaky_knees.blog.forms import CommentForm


@pytest.mark.django_db
class TestCommentForm:
    """Tests for comment form."""

    def test_comment_form_valid_data(self):
        """Test comment form with valid data."""
        form = CommentForm(
            data={"text": "This is a test comment"},
        )
        assert form.is_valid()

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
