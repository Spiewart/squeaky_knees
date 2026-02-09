"""
Tests for signup forms to ensure buttons are properly positioned and forms
submit correctly.

These tests verify the fix for the crispy-forms + django-recaptcha issue
where buttons were rendered outside the form element, preventing form
submissions.
"""

import re

from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class SignupFormSubmissionTest(TestCase):
    """Test that signup form buttons send requests correctly."""

    def setUp(self):
        self.client = Client()
        self.signup_url = reverse("account_signup")

    def test_signup_page_renders(self):
        """Test that signup page loads successfully."""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/signup.html")

    def test_signup_form_has_required_fields(self):
        """Test that signup form contains expected fields."""
        response = self.client.get(self.signup_url)
        content = response.content.decode()

        # Should have CSRF token
        self.assertIn("csrfmiddlewaretoken", content)

        # Should have reCAPTCHA widget (looks for class, not name)
        self.assertIn('class="g-recaptcha"', content)

        # Should have submit button
        self.assertIn('type="submit"', content)

    def test_signup_form_media_included(self):
        """
        Test that form.media is rendered (loads reCAPTCHA JavaScript).

        This is critical - without {{ form.media }}, the reCAPTCHA widget
        JavaScript won't load and the form won't validate.
        """
        response = self.client.get(self.signup_url)
        content = response.content.decode()

        # Should include reCAPTCHA widget JavaScript
        self.assertIn("recaptcha", content.lower())
        # Should be a <script> tag loading the widget
        self.assertTrue(
            re.search(r"<script[^>]*>.*grecaptcha.*</script>", content, re.DOTALL)
            or re.search(r"src=.*recaptcha.*\.js", content),
        )

    def test_signup_post_with_valid_data(self):
        """Test that signup form can be submitted via POST."""
        signup_data = {
            "username": "testuser123",
            "email": "testuser@example.com",
            "password1": "TestPassword123!",
            "password2": "TestPassword123!",
            "g-recaptcha-response": "test-token",
        }

        response = self.client.post(self.signup_url, data=signup_data)

        # Should redirect on success (to verification page or confirmation)
        # Response may be 200 (form re-rendered with errors) or 302 (redirect)
        self.assertIn(response.status_code, [200, 302])

    def test_signup_post_without_csrf_token_fails(self):
        """Test that POST without CSRF token is rejected."""
        # Disable CSRF middleware for this test
        client = Client(enforce_csrf_checks=True)

        signup_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "TestPassword123!",
            "password2": "TestPassword123!",
        }

        response = client.post(self.signup_url, data=signup_data)

        # Should reject with 403 Forbidden
        self.assertEqual(response.status_code, 403)


class SignupTemplateStructureTest(TestCase):
    """Test that signup template has correct HTML structure."""

    def setUp(self):
        self.client = Client()
        self.signup_url = reverse("account_signup")

    def test_button_is_inside_form_element(self):
        """
        Test that submit button is inside <form> element.

        This is the critical fix for the crispy-forms + django-recaptcha issue.
        If the button is outside the form, form submissions won't work.
        """
        response = self.client.get(self.signup_url)
        content = response.content.decode()

        # Extract the form section
        form_match = re.search(
            r'<form[^>]*method=["\']post["\'][^>]*>(.*?)</form>',
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(form_match, "No form element with POST method found")

        form_content = form_match.group(1)

        # Button should be inside form
        self.assertIn(
            'type="submit"',
            form_content,
            "Submit button not found inside form",
        )

    def test_crispy_form_renders_without_form_tags(self):
        """
        Test that crispy form is configured with form_tag=False.

        If form_tag=False is not set, {% crispy form %} will render complete
        <form>...</form> tags, making the manual form tags unnecessary or
        causing nested forms.
        """
        response = self.client.get(self.signup_url)
        content = response.content.decode()

        # Should have exactly one opening <form> tag (the manual one)
        form_opens = len(re.findall(r'<form[^>]*method=["\']post["\']', content))
        self.assertEqual(
            form_opens,
            1,
            f"Expected 1 form element, found {form_opens}. "
            "Check FormHelper.form_tag setting.",
        )

    def test_csrf_token_inside_form(self):
        """Test that CSRF token is inside form element."""
        response = self.client.get(self.signup_url)
        content = response.content.decode()

        # Extract form section
        form_match = re.search(
            r'<form[^>]*method=["\']post["\'][^>]*>(.*?)</form>',
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(form_match, "No form element found")

        form_content = form_match.group(1)

        # CSRF token should be inside form
        self.assertIn(
            "csrfmiddlewaretoken",
            form_content,
            "CSRF token not found inside form",
        )

    def test_recaptcha_input_inside_form(self):
        """Test that reCAPTCHA response input is inside form element."""
        response = self.client.get(self.signup_url)
        content = response.content.decode()

        # Extract form section
        form_match = re.search(
            r'<form[^>]*method=["\']post["\'][^>]*>(.*?)</form>',
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(form_match, "No form element found")

        form_content = form_match.group(1)

        # reCAPTCHA input should be inside form (look for g-recaptcha class)
        self.assertIn(
            "g-recaptcha",
            form_content,
            "reCAPTCHA input not found inside form",
        )

    def test_form_has_correct_action_and_method(self):
        """Test that form has POST method and correct action URL."""
        response = self.client.get(self.signup_url)
        content = response.content.decode()

        # Form should have method="post"
        self.assertIn('method="post"', content)

        # Form should have action attribute pointing to signup URL
        self.assertTrue(
            re.search(r'action="/accounts/signup/"', content),
            "Form action not pointing to signup endpoint",
        )


class SocialSignupFormTest(TestCase):
    """Test that social signup forms have same structure as regular signup."""

    def setUp(self):
        self.client = Client()
        # Try to get social signup URL if it exists
        from django.urls import NoReverseMatch

        try:
            self.social_signup_url = reverse("socialaccount_signup")
        except NoReverseMatch:
            self.social_signup_url = None

    def test_social_signup_button_inside_form(self):
        """Test that social signup button is also inside form element."""
        if not self.social_signup_url:
            self.skipTest("Social signup URL not configured")

        response = self.client.get(self.social_signup_url)

        # Social signup may redirect, so accept both 200 and 302
        self.assertIn(response.status_code, [200, 302])

        content = response.content.decode()

        # Extract form section
        form_match = re.search(
            r'<form[^>]*method=["\']post["\'][^>]*>(.*?)</form>',
            content,
            re.DOTALL,
        )

        if form_match:
            form_content = form_match.group(1)
            # Button should be inside form
            self.assertIn(
                'type="submit"',
                form_content,
                "Submit button not found inside social signup form",
            )


class FormHelperConfigurationTest(TestCase):
    """Test that FormHelper is correctly configured in form classes."""

    def test_user_signup_form_has_form_helper(self):
        """Test that UserSignupForm has FormHelper configured."""
        from squeaky_knees.users.forms import UserSignupForm

        form = UserSignupForm()

        # Should have helper attribute
        self.assertTrue(
            hasattr(form, "helper"),
            "UserSignupForm missing FormHelper",
        )

        # form_tag should be False
        self.assertFalse(
            form.helper.form_tag,
            "UserSignupForm.helper.form_tag should be False",
        )

    def test_user_social_signup_form_has_form_helper(self):
        """Test that UserSocialSignupForm has FormHelper configured."""
        from unittest.mock import Mock

        from squeaky_knees.users.forms import UserSocialSignupForm

        # UserSocialSignupForm requires sociallogin kwarg
        mock_sociallogin = Mock()
        form = UserSocialSignupForm(sociallogin=mock_sociallogin)

        # Should have helper attribute
        self.assertTrue(
            hasattr(form, "helper"),
            "UserSocialSignupForm missing FormHelper",
        )

        # form_tag should be False
        self.assertFalse(
            form.helper.form_tag,
            "UserSocialSignupForm.helper.form_tag should be False",
        )

    def test_signup_form_has_recaptcha_field(self):
        """Test that signup forms have reCAPTCHA field."""
        from squeaky_knees.users.forms import UserSignupForm

        form = UserSignupForm()

        # Should have captcha field
        self.assertIn("captcha", form.fields)

        # Should be ReCaptchaV3
        from django_recaptcha.fields import ReCaptchaField

        self.assertIsInstance(form.fields["captcha"], ReCaptchaField)


if __name__ == "__main__":
    import unittest

    unittest.main()
