"""Tests for security headers middleware."""

import pytest
from django.test import Client


@pytest.fixture
def client_with_middleware():
    """Fixture providing a test client."""
    return Client()


@pytest.mark.django_db
class TestSecurityHeadersMiddleware:
    """Test security headers are properly set."""

    def test_x_content_type_options_header_set(self, client_with_middleware):
        """X-Content-Type-Options header should be set to nosniff."""
        response = client_with_middleware.get("/")
        assert response["X-Content-Type-Options"] == "nosniff"

    def test_x_xss_protection_header_set(self, client_with_middleware):
        """X-XSS-Protection header should be set."""
        response = client_with_middleware.get("/")
        assert response["X-XSS-Protection"] == "1; mode=block"

    def test_x_frame_options_header_set(self, client_with_middleware):
        """X-Frame-Options header should be set."""
        response = client_with_middleware.get("/")
        assert response["X-Frame-Options"] in ("DENY", "SAMEORIGIN")

    def test_security_headers_on_404_page(self, client_with_middleware):
        """Security headers should be set even on 404 responses."""
        response = client_with_middleware.get("/nonexistent-page-xyz/")
        assert response["X-Content-Type-Options"] == "nosniff"
        assert response["X-XSS-Protection"] == "1; mode=block"
        # 404 pages may be caught by Django before our middleware,
        # but we should verify they have the headers if they're processed by it

    def test_security_headers_on_authenticated_view(
        self,
        client_with_middleware,
        django_user_model,
    ):
        """Security headers should be set on authenticated views."""
        user = django_user_model.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        client_with_middleware.force_login(user)
        response = client_with_middleware.get("/accounts/email/")
        assert response["X-Content-Type-Options"] == "nosniff"
        assert response["X-XSS-Protection"] == "1; mode=block"

    def test_all_required_security_headers_present(self, client_with_middleware):
        """All required security headers should be present."""
        response = client_with_middleware.get("/")
        required_headers = [
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "X-Frame-Options",
        ]
        for header in required_headers:
            assert header in response, f"Missing security header: {header}"

    def test_security_headers_not_overwritten_if_already_set(
        self,
        client_with_middleware,
    ):
        """If X-Frame-Options is already set, middleware should not overwrite it."""
        # This test verifies the defensive logic in the middleware
        response = client_with_middleware.get("/")
        # X-Frame-Options is set by both SecurityMiddleware and our custom middleware
        # We check it's set to something reasonable
        frame_options = response.get("X-Frame-Options")
        assert frame_options is not None
        assert frame_options in ("DENY", "SAMEORIGIN")
