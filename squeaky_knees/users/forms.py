from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.contrib.auth import forms as admin_forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

from config.ratelimit import is_rate_limited

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        error_messages = {
            "username": {"unique": _("This username has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """

    captcha = ReCaptchaField(
        widget=ReCaptchaV3(attrs={"data-action": "signup"}),
    )

    # Rate limit: 5 signup attempts per 3600 seconds (1 hour) per IP
    RATE_LIMIT_MAX_ATTEMPTS = 5
    RATE_LIMIT_WINDOW_SECONDS = 3600

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        """Add rate limiting check to signup form."""
        cleaned_data = super().clean()

        # Check rate limiting before other validations
        if self.request and is_rate_limited(
            self.request,
            "user_signup",
            self.RATE_LIMIT_MAX_ATTEMPTS,
            self.RATE_LIMIT_WINDOW_SECONDS,
        ):
            raise ValidationError(
                "Too many signup attempts. Please try again in a few hours.",
            )

        return cleaned_data


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """

    captcha = ReCaptchaField(
        widget=ReCaptchaV3(attrs={"data-action": "social_signup"}),
    )
