from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from crispy_forms.layout import Layout
from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

from .models import Comment


class CommentForm(forms.ModelForm):
    """Form for submitting comments on blog posts."""

    captcha = ReCaptchaField(
        widget=ReCaptchaV3(attrs={"data-action": "comments"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        """Convert plain text input to StreamField JSON format."""
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
                return parsed

        # Fallback: treat as plain text
        return [
            {
                "type": "rich_text",
                "value": f"<p>{escape(str(text_input))}</p>",
            }
        ]
