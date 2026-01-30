"""Module for all Form Tests."""

from django.test import RequestFactory
from django.utils.translation import gettext_lazy as _

from squeaky_knees.users.forms import UserAdminCreationForm
from squeaky_knees.users.models import User


class TestUserAdminCreationForm:
    """
    Test class for all tests related to the UserAdminCreationForm
    """

    def test_username_validation_error_msg(self, user: User):
        """
        Tests UserAdminCreation Form's unique validator functions correctly by testing:
            1) A new user with an existing username cannot be added.
            2) Only 1 error is raised by the UserCreation Form
            3) The desired error message is raised
        """

        # The user already exists,
        # hence cannot be created.
        form = UserAdminCreationForm(
            {
                "username": user.username,
                "password1": user.password,
                "password2": user.password,
            },
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "username" in form.errors
        assert form.errors["username"][0] == _("This username has already been taken.")


class TestSignupRecaptchaForms:
    """Tests for reCAPTCHA validation in signup forms."""

    def test_user_signup_form_has_captcha_field(self, rf: RequestFactory):
        """Test signup form includes reCAPTCHA field."""
        from squeaky_knees.users.forms import UserSignupForm

        request = rf.get("/accounts/signup/")
        form = UserSignupForm(request=request)
        assert "captcha" in form.fields

    def test_social_signup_form_has_captcha_field(self, rf: RequestFactory):
        """Test social signup form includes reCAPTCHA field."""
        from squeaky_knees.users.forms import UserSocialSignupForm

        request = rf.get("/accounts/social/signup/")
        form = UserSocialSignupForm(request=request)
        assert "captcha" in form.fields
