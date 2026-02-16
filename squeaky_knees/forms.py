from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from crispy_forms.layout import Layout
from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

from config.ratelimit import is_rate_limited


class ContactForm(forms.Form):
    """Contact form with reCAPTCHA v3 protection and rate limiting."""

    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 6}), max_length=5000)
    captcha = ReCaptchaField(
        widget=ReCaptchaV3(attrs={"data-action": "contact"}),
    )

    RATE_LIMIT_MAX_ATTEMPTS = 5
    RATE_LIMIT_WINDOW_SECONDS = 3600

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("name"),
            Field("email"),
            Field("message"),
            Field("captcha"),
        )

    def clean(self):
        cleaned_data = super().clean()
        if self.request and is_rate_limited(
            self.request,
            "contact_form",
            self.RATE_LIMIT_MAX_ATTEMPTS,
            self.RATE_LIMIT_WINDOW_SECONDS,
        ):
            rate_limit_msg = (
                "You are submitting contact forms too frequently. "
                "Please try again later."
            )
            raise forms.ValidationError(rate_limit_msg)
        return cleaned_data
