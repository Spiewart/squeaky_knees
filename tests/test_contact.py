"""Comprehensive unit and integration tests for the contact page feature."""

from unittest.mock import patch

import pytest
from django.conf import settings
from django.core import mail
from django.urls import resolve
from django.urls import reverse
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

from squeaky_knees.forms import ContactForm
from squeaky_knees.views import contact_success_view
from squeaky_knees.views import contact_view

# ---------------------------------------------------------------------------
# ContactForm unit tests
# ---------------------------------------------------------------------------


class TestContactFormFields:
    """Unit tests for ContactForm field configuration."""

    def test_has_expected_fields(self):
        form = ContactForm()
        assert set(form.fields.keys()) == {"name", "email", "message", "captcha"}

    def test_name_max_length(self):
        form = ContactForm()
        assert form.fields["name"].max_length == 100

    def test_email_field_type(self):
        from django.forms import EmailField

        form = ContactForm()
        assert isinstance(form.fields["email"], EmailField)

    def test_message_max_length(self):
        form = ContactForm()
        assert form.fields["message"].max_length == 5000

    def test_message_widget_is_textarea(self):
        from django.forms import Textarea

        form = ContactForm()
        assert isinstance(form.fields["message"].widget, Textarea)

    def test_message_textarea_rows(self):
        form = ContactForm()
        assert form.fields["message"].widget.attrs.get("rows") == 6

    def test_captcha_field_type(self):
        form = ContactForm()
        assert isinstance(form.fields["captcha"], ReCaptchaField)

    def test_captcha_uses_v3_widget(self):
        form = ContactForm()
        assert isinstance(form.fields["captcha"].widget, ReCaptchaV3)

    def test_captcha_data_action_is_contact(self):
        form = ContactForm()
        assert form.fields["captcha"].widget.attrs["data-action"] == "contact"


class TestContactFormHelper:
    """Unit tests for ContactForm crispy FormHelper configuration."""

    def test_has_form_helper(self):
        form = ContactForm()
        assert hasattr(form, "helper")

    def test_helper_has_layout(self):
        form = ContactForm()
        assert form.helper.layout is not None

    def test_helper_form_tag_is_false(self):
        """form_tag must be False so template controls <form> tags."""
        form = ContactForm()
        assert form.helper.form_tag is False


class TestContactFormValidation:
    """Unit tests for ContactForm validation logic."""

    def test_valid_data(self):
        form = ContactForm(
            data={
                "name": "Test User",
                "email": "test@example.com",
                "message": "Hello, this is a test message.",
                "g-recaptcha-response": "test-token",
            },
        )
        assert form.is_valid()

    def test_name_required(self):
        form = ContactForm(
            data={
                "email": "test@example.com",
                "message": "Hello",
                "g-recaptcha-response": "test-token",
            },
        )
        assert not form.is_valid()
        assert "name" in form.errors

    def test_email_required(self):
        form = ContactForm(
            data={
                "name": "Test User",
                "message": "Hello",
                "g-recaptcha-response": "test-token",
            },
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_message_required(self):
        form = ContactForm(
            data={
                "name": "Test User",
                "email": "test@example.com",
                "g-recaptcha-response": "test-token",
            },
        )
        assert not form.is_valid()
        assert "message" in form.errors

    def test_invalid_email_format(self):
        form = ContactForm(
            data={
                "name": "Test User",
                "email": "not-an-email",
                "message": "Hello",
                "g-recaptcha-response": "test-token",
            },
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_name_exceeds_max_length(self):
        form = ContactForm(
            data={
                "name": "A" * 101,
                "email": "test@example.com",
                "message": "Hello",
                "g-recaptcha-response": "test-token",
            },
        )
        assert not form.is_valid()
        assert "name" in form.errors

    def test_message_exceeds_max_length(self):
        form = ContactForm(
            data={
                "name": "Test User",
                "email": "test@example.com",
                "message": "A" * 5001,
                "g-recaptcha-response": "test-token",
            },
        )
        assert not form.is_valid()
        assert "message" in form.errors

    def test_name_at_max_length_is_valid(self):
        form = ContactForm(
            data={
                "name": "A" * 100,
                "email": "test@example.com",
                "message": "Hello",
                "g-recaptcha-response": "test-token",
            },
        )
        assert form.is_valid()

    def test_message_at_max_length_is_valid(self):
        form = ContactForm(
            data={
                "name": "Test User",
                "email": "test@example.com",
                "message": "A" * 5000,
                "g-recaptcha-response": "test-token",
            },
        )
        assert form.is_valid()

    def test_empty_form_is_invalid(self):
        form = ContactForm(data={})
        assert not form.is_valid()
        assert "name" in form.errors
        assert "email" in form.errors
        assert "message" in form.errors


# ---------------------------------------------------------------------------
# URL routing tests
# ---------------------------------------------------------------------------


class TestContactUrlRouting:
    """Tests for contact URL configuration."""

    def test_contact_url_resolves_to_view(self):
        match = resolve("/contact/")
        assert match.func == contact_view

    def test_contact_url_reverse(self):
        assert reverse("contact") == "/contact/"

    def test_contact_success_url_resolves_to_view(self):
        match = resolve("/contact/success/")
        assert match.func == contact_success_view

    def test_contact_success_url_reverse(self):
        assert reverse("contact_success") == "/contact/success/"


# ---------------------------------------------------------------------------
# contact_view integration tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestContactViewGet:
    """Tests for GET requests to contact_view."""

    def test_get_returns_200(self, client):
        response = client.get(reverse("contact"))
        assert response.status_code == 200

    def test_get_uses_correct_template(self, client):
        response = client.get(reverse("contact"))
        assert any(t.name == "pages/contact.html" for t in response.templates)

    def test_get_contains_form(self, client):
        response = client.get(reverse("contact"))
        assert "form" in response.context

    def test_get_form_is_contact_form(self, client):
        response = client.get(reverse("contact"))
        assert isinstance(response.context["form"], ContactForm)

    def test_get_form_is_unbound(self, client):
        response = client.get(reverse("contact"))
        assert not response.context["form"].is_bound

    def test_get_renders_form_fields(self, client):
        response = client.get(reverse("contact"))
        content = response.content.decode()
        assert 'name="name"' in content
        assert 'name="email"' in content
        assert 'name="message"' in content

    def test_get_renders_submit_button(self, client):
        response = client.get(reverse("contact"))
        content = response.content.decode()
        assert "Send Message" in content

    def test_get_has_csrf_token(self, client):
        response = client.get(reverse("contact"))
        content = response.content.decode()
        assert "csrfmiddlewaretoken" in content

    def test_get_has_manual_form_tag(self, client):
        """Template should use manual <form> tags, not crispy form_tag."""
        response = client.get(reverse("contact"))
        content = response.content.decode()
        assert 'method="post"' in content
        assert 'action="/contact/"' in content

    def test_get_submit_button_inside_form(self, client):
        """Submit button must be inside the <form> element for reCAPTCHA v3 to work."""
        response = client.get(reverse("contact"))
        content = response.content.decode()
        # Find the form element and verify button is inside
        form_start = content.find('<form method="post"')
        form_end = content.find("</form>", form_start)
        form_html = content[form_start:form_end]
        assert "Send Message" in form_html

    def test_get_page_title(self, client):
        response = client.get(reverse("contact"))
        content = response.content.decode()
        assert "<title>" in content
        assert "Contact" in content


@pytest.mark.django_db
@pytest.mark.usefixtures("clear_cache")
class TestContactViewPostSuccess:
    """Tests for successful POST to contact_view."""

    VALID_DATA = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "message": "I have a question about your research.",
        "g-recaptcha-response": "test-token",
    }

    def test_post_valid_data_redirects_to_success(self, client):
        response = client.post(reverse("contact"), data=self.VALID_DATA)
        assert response.status_code == 302
        assert response.url == reverse("contact_success")

    def test_post_valid_data_sends_email(self, client):
        mail.outbox = []
        client.post(reverse("contact"), data=self.VALID_DATA)
        assert len(mail.outbox) == 1

    def test_email_subject_includes_name(self, client):
        mail.outbox = []
        client.post(reverse("contact"), data=self.VALID_DATA)
        assert "Jane Doe" in mail.outbox[0].subject

    def test_email_sent_to_admin(self, client):
        mail.outbox = []
        client.post(reverse("contact"), data=self.VALID_DATA)
        expected_recipient = settings.ADMINS[0][1]
        assert expected_recipient in mail.outbox[0].to

    def test_email_from_default_address(self, client):
        mail.outbox = []
        client.post(reverse("contact"), data=self.VALID_DATA)
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_email_is_html(self, client):
        mail.outbox = []
        client.post(reverse("contact"), data=self.VALID_DATA)
        # send_mail with html_message creates an alternative
        assert mail.outbox[0].alternatives

    def test_email_html_contains_name(self, client):
        mail.outbox = []
        client.post(reverse("contact"), data=self.VALID_DATA)
        html_body = mail.outbox[0].alternatives[0][0]
        assert "Jane Doe" in html_body

    def test_email_html_contains_email(self, client):
        mail.outbox = []
        client.post(reverse("contact"), data=self.VALID_DATA)
        html_body = mail.outbox[0].alternatives[0][0]
        assert "jane@example.com" in html_body

    def test_email_html_contains_message(self, client):
        mail.outbox = []
        client.post(reverse("contact"), data=self.VALID_DATA)
        html_body = mail.outbox[0].alternatives[0][0]
        assert "I have a question about your research." in html_body

    def test_email_html_has_mailto_link(self, client):
        mail.outbox = []
        client.post(reverse("contact"), data=self.VALID_DATA)
        html_body = mail.outbox[0].alternatives[0][0]
        assert "mailto:jane@example.com" in html_body

    def test_session_stores_submission_data(self, client):
        client.post(reverse("contact"), data=self.VALID_DATA)
        session = client.session
        assert session["contact_success"]["name"] == "Jane Doe"
        assert session["contact_success"]["email"] == "jane@example.com"
        assert (
            session["contact_success"]["message"]
            == "I have a question about your research."
        )

    def test_prg_pattern_follows_redirect_to_success(self, client):
        """After successful POST, following the redirect lands on the success page."""
        response = client.post(reverse("contact"), data=self.VALID_DATA, follow=True)
        assert response.status_code == 200
        assert any(t.name == "pages/contact_success.html" for t in response.templates)


@pytest.mark.django_db
class TestContactViewPostInvalid:
    """Tests for invalid POST to contact_view."""

    def test_missing_name_rerenders_form(self, client):
        response = client.post(
            reverse("contact"),
            data={
                "email": "test@example.com",
                "message": "Hello",
                "g-recaptcha-response": "test-token",
            },
        )
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_missing_email_rerenders_form(self, client):
        response = client.post(
            reverse("contact"),
            data={
                "name": "Test",
                "message": "Hello",
                "g-recaptcha-response": "test-token",
            },
        )
        assert response.status_code == 200
        assert "email" in response.context["form"].errors

    def test_missing_message_rerenders_form(self, client):
        response = client.post(
            reverse("contact"),
            data={
                "name": "Test",
                "email": "test@example.com",
                "g-recaptcha-response": "test-token",
            },
        )
        assert response.status_code == 200
        assert "message" in response.context["form"].errors

    def test_invalid_email_rerenders_form(self, client):
        response = client.post(
            reverse("contact"),
            data={
                "name": "Test",
                "email": "not-valid",
                "message": "Hello",
                "g-recaptcha-response": "test-token",
            },
        )
        assert response.status_code == 200
        assert "email" in response.context["form"].errors

    def test_empty_post_rerenders_form(self, client):
        response = client.post(reverse("contact"), data={})
        assert response.status_code == 200
        form = response.context["form"]
        assert "name" in form.errors
        assert "email" in form.errors
        assert "message" in form.errors

    def test_invalid_post_does_not_send_email(self, client):
        mail.outbox = []
        client.post(reverse("contact"), data={})
        assert len(mail.outbox) == 0

    def test_invalid_post_preserves_submitted_values(self, client):
        """Form should re-populate with submitted data on validation failure."""
        response = client.post(
            reverse("contact"),
            data={
                "name": "Jane Doe",
                "email": "not-valid",
                "message": "My message",
                "g-recaptcha-response": "test-token",
            },
        )
        form = response.context["form"]
        assert form["name"].value() == "Jane Doe"
        assert form["message"].value() == "My message"


@pytest.mark.django_db
@pytest.mark.usefixtures("clear_cache")
class TestContactViewEmailFailure:
    """Tests for email sending failure in contact_view."""

    VALID_DATA = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "message": "Test message.",
        "g-recaptcha-response": "test-token",
    }

    @patch("squeaky_knees.views.send_mail", side_effect=OSError("SMTP error"))
    def test_email_failure_rerenders_form(self, mock_send, client):
        response = client.post(reverse("contact"), data=self.VALID_DATA)
        # Should NOT redirect -- re-renders the form page
        assert response.status_code == 200

    @patch("squeaky_knees.views.send_mail", side_effect=OSError("SMTP error"))
    def test_email_failure_shows_error_message(self, mock_send, client):
        response = client.post(reverse("contact"), data=self.VALID_DATA)
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "problem sending" in str(messages[0]).lower()

    @patch("squeaky_knees.views.send_mail", side_effect=OSError("SMTP error"))
    def test_email_failure_message_tag(self, mock_send, client):
        response = client.post(reverse("contact"), data=self.VALID_DATA)
        messages = list(response.context["messages"])
        assert messages[0].tags == "error"

    @patch("squeaky_knees.views.send_mail", side_effect=OSError("SMTP error"))
    def test_email_failure_form_is_bound(self, mock_send, client):
        """Form should keep the user's data so they can retry."""
        response = client.post(reverse("contact"), data=self.VALID_DATA)
        form = response.context["form"]
        assert form.is_bound
        assert form["name"].value() == "Jane Doe"


# ---------------------------------------------------------------------------
# contact_success_view integration tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestContactSuccessView:
    """Tests for the contact success page."""

    def test_with_session_data_renders_success_page(self, client):
        session = client.session
        session["contact_success"] = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "message": "My test message.",
        }
        session.save()

        response = client.get(reverse("contact_success"))
        assert response.status_code == 200
        assert any(t.name == "pages/contact_success.html" for t in response.templates)

    def test_displays_submitted_name(self, client):
        session = client.session
        session["contact_success"] = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "message": "My test message.",
        }
        session.save()

        response = client.get(reverse("contact_success"))
        assert "Jane Doe" in response.content.decode()

    def test_displays_submitted_email(self, client):
        session = client.session
        session["contact_success"] = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "message": "My test message.",
        }
        session.save()

        response = client.get(reverse("contact_success"))
        assert "jane@example.com" in response.content.decode()

    def test_displays_submitted_message(self, client):
        session = client.session
        session["contact_success"] = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "message": "My test message.",
        }
        session.save()

        response = client.get(reverse("contact_success"))
        assert "My test message." in response.content.decode()

    def test_session_data_consumed_after_display(self, client):
        """Session data should be removed after the success page is displayed."""
        session = client.session
        session["contact_success"] = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "message": "My test message.",
        }
        session.save()

        client.get(reverse("contact_success"))

        # Session data should be gone now
        session = client.session
        assert "contact_success" not in session

    def test_refresh_redirects_to_contact(self, client):
        """Second visit (after session consumed) should redirect back to contact."""
        session = client.session
        session["contact_success"] = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "message": "My test message.",
        }
        session.save()

        client.get(reverse("contact_success"))  # first visit consumes session

        response = client.get(reverse("contact_success"))  # second visit
        assert response.status_code == 302
        assert response.url == reverse("contact")

    def test_direct_access_without_session_redirects(self, client):
        """Visiting /contact/success/ without session redirects."""
        response = client.get(reverse("contact_success"))
        assert response.status_code == 302
        assert response.url == reverse("contact")

    def test_has_return_home_link(self, client):
        session = client.session
        session["contact_success"] = {
            "name": "Jane",
            "email": "j@example.com",
            "message": "Hi",
        }
        session.save()

        response = client.get(reverse("contact_success"))
        content = response.content.decode()
        assert "Return to Home" in content
        assert 'href="/"' in content

    def test_has_blog_link(self, client):
        session = client.session
        session["contact_success"] = {
            "name": "Jane",
            "email": "j@example.com",
            "message": "Hi",
        }
        session.save()

        response = client.get(reverse("contact_success"))
        content = response.content.decode()
        assert "Visit Blog" in content
        assert 'href="/blog/"' in content


# ---------------------------------------------------------------------------
# Rate limiting tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestContactRateLimiting:
    """Tests for contact form rate limiting."""

    VALID_DATA = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "message": "Test message.",
        "g-recaptcha-response": "test-token",
    }

    def test_form_has_rate_limit_constants(self):
        assert hasattr(ContactForm, "RATE_LIMIT_MAX_ATTEMPTS")
        assert hasattr(ContactForm, "RATE_LIMIT_WINDOW_SECONDS")
        assert ContactForm.RATE_LIMIT_MAX_ATTEMPTS == 5
        assert ContactForm.RATE_LIMIT_WINDOW_SECONDS == 3600

    def test_form_accepts_request_kwarg(self):
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/contact/")
        form = ContactForm(request=request)
        assert form.request is request

    def test_form_without_request_is_valid(self):
        """Form without request should still validate (no rate limiting applied)."""
        form = ContactForm(
            data=self.VALID_DATA,
        )
        assert form.is_valid()

    @patch("squeaky_knees.forms.is_rate_limited", return_value=True)
    def test_rate_limited_form_is_invalid(self, mock_rate_limit):
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post("/contact/", data=self.VALID_DATA)
        form = ContactForm(data=self.VALID_DATA, request=request)
        assert not form.is_valid()
        assert "__all__" in form.errors
        assert "too frequently" in str(form.errors["__all__"])

    @patch("squeaky_knees.forms.is_rate_limited", return_value=True)
    def test_rate_limited_does_not_send_email(self, mock_rate_limit, client):
        mail.outbox = []
        client.post(reverse("contact"), data=self.VALID_DATA)
        assert len(mail.outbox) == 0

    @patch("squeaky_knees.forms.is_rate_limited", return_value=True)
    def test_rate_limited_rerenders_form(self, mock_rate_limit, client):
        response = client.post(reverse("contact"), data=self.VALID_DATA)
        assert response.status_code == 200
        assert response.context["form"].errors

    @patch("squeaky_knees.forms.is_rate_limited", return_value=False)
    def test_not_rate_limited_proceeds_normally(self, mock_rate_limit, client):
        mail.outbox = []
        response = client.post(reverse("contact"), data=self.VALID_DATA)
        assert response.status_code == 302
        assert len(mail.outbox) == 1

    @patch("squeaky_knees.forms.is_rate_limited", return_value=True)
    def test_rate_limit_calls_with_correct_action(self, mock_rate_limit):
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post("/contact/", data=self.VALID_DATA)
        form = ContactForm(data=self.VALID_DATA, request=request)
        form.is_valid()

        mock_rate_limit.assert_called_once_with(
            request,
            "contact_form",
            ContactForm.RATE_LIMIT_MAX_ATTEMPTS,
            ContactForm.RATE_LIMIT_WINDOW_SECONDS,
        )


# ---------------------------------------------------------------------------
# Template integration tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFooterContactLink:
    """Tests for the Contact link in the site-wide footer."""

    def test_footer_on_home_page(self, client):
        response = client.get(reverse("home"))
        content = response.content.decode()
        assert "<footer" in content
        assert 'href="/contact/"' in content

    def test_footer_on_about_page(self, client):
        response = client.get(reverse("about"))
        content = response.content.decode()
        assert "<footer" in content
        assert 'href="/contact/"' in content

    def test_footer_on_contact_page(self, client):
        response = client.get(reverse("contact"))
        content = response.content.decode()
        assert "<footer" in content
        assert 'href="/contact/"' in content

    def test_footer_on_blog_page(self, client, blog_index):
        response = client.get(reverse("blog_index"))
        content = response.content.decode()
        assert "<footer" in content
        assert 'href="/contact/"' in content

    def test_footer_link_text(self, client):
        response = client.get(reverse("home"))
        content = response.content.decode()
        assert ">Contact<" in content


@pytest.mark.django_db
class TestHomepageContactButton:
    """Tests for the Contact button in the homepage jumbotron."""

    def test_contact_button_present(self, client):
        response = client.get(reverse("home"))
        content = response.content.decode()
        assert 'href="/contact/"' in content
        assert "Contact" in content

    def test_contact_button_is_styled(self, client):
        response = client.get(reverse("home"))
        content = response.content.decode()
        # Button should have Bootstrap button classes
        assert "btn" in content
        assert "btn-outline-secondary" in content

    def test_contact_button_in_jumbotron(self, client):
        """The Contact button should be inside the jumbotron d-flex row."""
        response = client.get(reverse("home"))
        content = response.content.decode()
        # Find the jumbotron flex container and verify Contact is nearby
        jumbotron_start = content.find("d-flex flex-wrap gap-2")
        assert jumbotron_start != -1
        # Find the closing tag of the flex container
        jumbotron_end = content.find("</div>", jumbotron_start)
        jumbotron_section = content[jumbotron_start:jumbotron_end]
        assert "/contact/" in jumbotron_section


# ---------------------------------------------------------------------------
# reCAPTCHA consistency test (extends existing pattern)
# ---------------------------------------------------------------------------


class TestContactFormRecaptchaConsistency:
    """Ensure ContactForm follows the same reCAPTCHA pattern as other forms."""

    def test_contact_form_has_captcha_field(self):
        form = ContactForm()
        assert "captcha" in form.fields
        assert isinstance(form.fields["captcha"], ReCaptchaField)

    def test_contact_form_uses_v3(self):
        form = ContactForm()
        assert isinstance(form.fields["captcha"].widget, ReCaptchaV3)

    def test_contact_form_action_is_contact(self):
        form = ContactForm()
        assert form.fields["captcha"].widget.attrs["data-action"] == "contact"
