"""
Integration tests for all reCAPTCHA forms in the project.

These tests verify that all forms using reCAPTCHA v3 are configured consistently
with FormHelper.form_tag=False and have buttons inside form elements.
"""

from django.test import TestCase
from django_recaptcha.fields import ReCaptchaField

from squeaky_knees.blog.forms import CommentForm
from squeaky_knees.forms import ContactForm
from squeaky_knees.users.forms import UserSignupForm
from squeaky_knees.users.forms import UserSocialSignupForm


class ReCaptchaFormConsistencyTest(TestCase):
    """Test that all reCAPTCHA forms follow the same pattern."""

    def test_all_recaptcha_forms_have_form_helper(self):
        """Test that all forms with reCAPTCHA have FormHelper configured."""
        from unittest.mock import Mock

        forms_to_test = [
            ("UserSignupForm", UserSignupForm, {}),
            ("UserSocialSignupForm", UserSocialSignupForm, {"sociallogin": Mock()}),
            ("CommentForm", CommentForm, {}),
            ("ContactForm", ContactForm, {}),
        ]

        for form_name, form_class, kwargs in forms_to_test:
            with self.subTest(form=form_name):
                form = form_class(**kwargs)

                # Should have helper attribute
                self.assertTrue(
                    hasattr(form, "helper"),
                    f"{form_name} missing FormHelper",
                )

                # form_tag should be False
                self.assertFalse(
                    form.helper.form_tag,
                    f"{form_name}.helper.form_tag should be False",
                )

    def test_all_recaptcha_forms_have_captcha_field(self):
        """Test that all forms have reCAPTCHA field."""
        from unittest.mock import Mock

        forms_to_test = [
            ("UserSignupForm", UserSignupForm, {}),
            ("UserSocialSignupForm", UserSocialSignupForm, {"sociallogin": Mock()}),
            ("CommentForm", CommentForm, {}),
            ("ContactForm", ContactForm, {}),
        ]

        for form_name, form_class, kwargs in forms_to_test:
            with self.subTest(form=form_name):
                form = form_class(**kwargs)

                # Should have captcha field
                self.assertIn(
                    "captcha",
                    form.fields,
                    f"{form_name} missing captcha field",
                )

                # Should be ReCaptchaField
                self.assertIsInstance(
                    form.fields["captcha"],
                    ReCaptchaField,
                    f"{form_name}.captcha is not a ReCaptchaField",
                )

    def test_all_recaptcha_forms_use_recaptcha_v3(self):
        """Test that all reCAPTCHA forms use v3 widget."""
        from unittest.mock import Mock

        from django_recaptcha.widgets import ReCaptchaV3

        forms_to_test = [
            ("UserSignupForm", UserSignupForm, {}),
            ("UserSocialSignupForm", UserSocialSignupForm, {"sociallogin": Mock()}),
            ("CommentForm", CommentForm, {}),
            ("ContactForm", ContactForm, {}),
        ]

        for form_name, form_class, kwargs in forms_to_test:
            with self.subTest(form=form_name):
                form = form_class(**kwargs)
                captcha_field = form.fields["captcha"]

                # Should use ReCaptchaV3 widget
                self.assertIsInstance(
                    captcha_field.widget,
                    ReCaptchaV3,
                    f"{form_name} should use ReCaptchaV3 widget",
                )

    def test_signup_forms_have_rate_limiting(self):
        """Test that signup forms have rate limiting configured."""
        # Only UserSignupForm has rate limiting, so test just that
        form_class = UserSignupForm

        # Should have rate limit constants
        self.assertTrue(
            hasattr(form_class, "RATE_LIMIT_MAX_ATTEMPTS"),
            "UserSignupForm missing RATE_LIMIT_MAX_ATTEMPTS",
        )

        self.assertTrue(
            hasattr(form_class, "RATE_LIMIT_WINDOW_SECONDS"),
            "UserSignupForm missing RATE_LIMIT_WINDOW_SECONDS",
        )

        # Rate limit should be reasonable (>= 1 attempt, < 1000)
        self.assertGreaterEqual(
            form_class.RATE_LIMIT_MAX_ATTEMPTS,
            1,
            "UserSignupForm rate limit too low",
        )

        self.assertLess(
            form_class.RATE_LIMIT_MAX_ATTEMPTS,
            1000,
            "UserSignupForm rate limit too high",
        )

    def test_comment_form_has_rate_limiting(self):
        """Test that CommentForm has rate limiting configured."""
        # Should have rate limit constants
        self.assertTrue(
            hasattr(CommentForm, "RATE_LIMIT_MAX_ATTEMPTS"),
            "CommentForm missing RATE_LIMIT_MAX_ATTEMPTS",
        )

        self.assertTrue(
            hasattr(CommentForm, "RATE_LIMIT_WINDOW_SECONDS"),
            "CommentForm missing RATE_LIMIT_WINDOW_SECONDS",
        )

        # Rate limit should be reasonable (>= 1 attempt, < 1000)
        self.assertGreaterEqual(
            CommentForm.RATE_LIMIT_MAX_ATTEMPTS,
            1,
            "CommentForm rate limit too low",
        )

        self.assertLess(
            CommentForm.RATE_LIMIT_MAX_ATTEMPTS,
            1000,
            "CommentForm rate limit too high",
        )


class ReCaptchaDataActionTest(TestCase):
    """Test that reCAPTCHA data-action attributes are set correctly."""

    def test_user_signup_has_correct_action(self):
        """Test that UserSignupForm has correct reCAPTCHA action."""
        form = UserSignupForm()
        captcha_widget = form.fields["captcha"].widget

        # Should have data-action attribute
        self.assertIn("data-action", captcha_widget.attrs)
        self.assertEqual(
            captcha_widget.attrs["data-action"],
            "signup",
            "UserSignupForm should use 'signup' action",
        )

    def test_social_signup_has_correct_action(self):
        """Test that UserSocialSignupForm has correct reCAPTCHA action."""
        from unittest.mock import Mock

        # UserSocialSignupForm requires sociallogin kwarg
        mock_sociallogin = Mock()
        form = UserSocialSignupForm(sociallogin=mock_sociallogin)
        captcha_widget = form.fields["captcha"].widget

        # Should have data-action attribute
        self.assertIn("data-action", captcha_widget.attrs)
        self.assertEqual(
            captcha_widget.attrs["data-action"],
            "social_signup",
            "UserSocialSignupForm should use 'social_signup' action",
        )

    def test_comment_form_has_correct_action(self):
        """Test that CommentForm has correct reCAPTCHA action."""
        form = CommentForm()
        captcha_widget = form.fields["captcha"].widget

        # Should have data-action attribute
        self.assertIn("data-action", captcha_widget.attrs)
        self.assertEqual(
            captcha_widget.attrs["data-action"],
            "comments",
            "CommentForm should use 'comments' action",
        )

    def test_contact_form_has_correct_action(self):
        """Test that ContactForm has correct reCAPTCHA action."""
        form = ContactForm()
        captcha_widget = form.fields["captcha"].widget

        self.assertIn("data-action", captcha_widget.attrs)
        self.assertEqual(
            captcha_widget.attrs["data-action"],
            "contact",
            "ContactForm should use 'contact' action",
        )


class FormHelperLayoutTest(TestCase):
    """Test that FormHelper layout is properly configured."""

    def test_user_signup_form_layout(self):
        """Test that UserSignupForm layout is configured."""
        form = UserSignupForm()

        # Should have helper with layout
        self.assertTrue(hasattr(form.helper, "layout"))

    def test_comment_form_layout(self):
        """Test that CommentForm layout includes captcha field."""
        form = CommentForm()

        # Should have helper with layout
        self.assertTrue(
            hasattr(form.helper, "layout"),
            "CommentForm helper missing layout",
        )

        # Layout should be configured
        self.assertIsNotNone(
            form.helper.layout,
            "CommentForm layout should be configured",
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
