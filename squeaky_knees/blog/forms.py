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
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't render the <form> tag
        self.helper.layout = Layout(
            Field("text", css_class="form-control", rows="4"),
            Field("captcha"),
        )

    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Leave a comment...",
                },
            ),
        }
        labels = {
            "text": "Your Comment",
        }
