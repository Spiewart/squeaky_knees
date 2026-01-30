"""Custom reCAPTCHA widgets for django-recaptcha integration.

Note: django-recaptcha's ReCaptchaV3 widget already respects RECAPTCHA_DISABLE
setting for local development and testing.
"""

from django_recaptcha.widgets import ReCaptchaV3  # noqa: F401
