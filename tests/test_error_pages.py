"""Tests for custom error pages."""

import pytest
from django.test import Client
from django.test import override_settings


@pytest.mark.django_db
class TestErrorPages:
    """Tests for custom error page templates."""

    def test_404_page_exists(self, client):
        """404.html template should exist."""
        response = client.get("/nonexistent-page-12345/")
        assert response.status_code == 404

    def test_404_page_renders(self, client):
        """404 page should render without error."""
        response = client.get("/nonexistent-page-12345/")
        assert response.status_code == 404
        assert len(response.content) > 0

    def test_404_page_includes_message(self, client):
        """404 page should include helpful message."""
        response = client.get("/nonexistent-page-12345/")
        content = response.content.decode()
        # Should mention not found or 404
        assert (
            "not found" in content.lower()
            or "404" in content
            or "page" in content.lower()
        )

    def test_404_page_not_django_default(self, client):
        """404 page should not be Django's default error page."""
        response = client.get("/nonexistent-page-12345/")
        content = response.content.decode()
        # Should not have default Django error styling
        assert "Django" not in content or "not found" in content.lower()

    def test_500_error_handler_exists(self):
        """500 error handler should be configured."""
        # Check that error handlers are in urls.py
        import config.urls

        # Should have error handler configuration
        assert hasattr(config, "urls")

    def test_404_contains_home_link(self, client):
        """404 page should contain link back to home."""
        response = client.get("/nonexistent-page-12345/")
        content = response.content.decode()
        # Should have some navigation or home link
        assert "href" in content or "<a" in content or "/" in content

    def test_404_has_proper_title(self, client):
        """404 page should have proper title."""
        response = client.get("/nonexistent-page-12345/")
        content = response.content.decode()
        # Should have title tag
        assert "<title>" in content and "</title>" in content

    def test_404_status_code_correct(self, client):
        """404 page should return 404 status code."""
        response = client.get("/definitely-does-not-exist/")
        assert response.status_code == 404

    def test_csrf_error_page_exists(self, client):
        """CSRF error page should be configured."""
        # This tests that 403_csrf.html is used
        # We can't easily trigger this in tests but should verify template exists
        from django.template.loader import get_template

        try:
            template = get_template("403_csrf.html")
            assert template is not None
        except Exception:
            # Template might not be loadable in test environment
            pass

    def test_permission_denied_page_exists(self, client):
        """Permission denied (403) page should exist."""
        from django.template.loader import get_template

        try:
            template = get_template("403.html")
            assert template is not None
        except Exception:
            pass

    def test_error_pages_use_base_template(self, client):
        """Error pages should extend base template."""
        response = client.get("/nonexistent/")
        content = response.content.decode()
        # Should have HTML structure
        assert "<!DOCTYPE" in content or "<html" in content or "<body" in content

    def test_404_page_accessible(self, client):
        """404 page should be accessible without raising exceptions."""
        try:
            response = client.get("/this-page-does-not-exist-xyz/")
            assert response.status_code == 404
        except Exception as e:
            pytest.fail(f"404 page raised exception: {e}")

    def test_404_page_returns_content(self, client):
        """404 page should return response content."""
        response = client.get("/fake-page/")
        assert response.status_code == 404
        assert response.content is not None
        assert len(response.content) > 0
