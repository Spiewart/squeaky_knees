from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from crispy_forms.layout import Layout
from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

from config.ratelimit import is_rate_limited
from config.validation import sanitize_streamfield_blocks
from config.validation import validate_comment_length

from .models import Comment


class CommentForm(forms.ModelForm):
    """Form for submitting comments on blog posts."""

    captcha = ReCaptchaField(
        widget=ReCaptchaV3(attrs={"data-action": "comments"}),
    )

    # Rate limit: 10 comments per 3600 seconds (1 hour) per user
    RATE_LIMIT_MAX_ATTEMPTS = 10
    RATE_LIMIT_WINDOW_SECONDS = 3600

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        # Replace StreamField form field with plain text field to bypass StreamField validation
        self.fields["text"] = forms.CharField(
            label="Your Comment",
            widget=forms.HiddenInput(attrs={"id": "comment-text-json"}),
            required=True,
        )
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't render the <form> tag
        self.helper.layout = Layout(
            Field("text", css_class="form-control", rows="4"),
            Field("captcha"),
        )

    class Meta:
        model = Comment
        fields = ["text"]
        labels = {
            "text": "Your Comment",
        }

    def clean_text(self):
        """Convert plain text input to StreamField JSON format and validate."""
        # Check rate limiting before validating content
        if self.request and is_rate_limited(
            self.request,
            "comment_add",
            self.RATE_LIMIT_MAX_ATTEMPTS,
            self.RATE_LIMIT_WINDOW_SECONDS,
        ):
            raise forms.ValidationError(
                "You are posting comments too frequently. Please try again in a few minutes.",
            )

        text_input = self.cleaned_data.get("text")
        if not text_input:
            raise forms.ValidationError("Comment cannot be empty.")

        import json
        from html import escape

        # Accept JSON StreamField payloads from the lightweight editor
        if isinstance(text_input, str):
            try:
                parsed = json.loads(text_input)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                if not parsed:
                    raise forms.ValidationError("Comment cannot be empty.")
                # Sanitize and validate blocks
                sanitized, errors = sanitize_streamfield_blocks(parsed)
                if errors:
                    raise forms.ValidationError(f"Invalid comment format: {errors[0]}")
                # Validate total comment length
                is_valid, error_msg = validate_comment_length(sanitized)
                if not is_valid:
                    raise forms.ValidationError(error_msg)
                return sanitized

        # Fallback: treat as plain text
        blocks = [
            {
                "type": "rich_text",
                "value": f"<p>{escape(str(text_input))}</p>",
            },
        ]
        # Validate fallback blocks
        is_valid, error_msg = validate_comment_length(blocks)
        if not is_valid:
            raise forms.ValidationError(error_msg)
        return blocks
