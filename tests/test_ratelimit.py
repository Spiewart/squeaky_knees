"""Tests for rate limiting functionality."""

import pytest
from django.core.cache import cache

from config.ratelimit import get_client_ip
from config.ratelimit import get_identifier_for_user_action
from config.ratelimit import get_rate_limit_info
from config.ratelimit import is_rate_limited


@pytest.fixture
def clear_cache():
    """Clear cache before and after each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestRateLimitingUtilities:
    """Test rate limiting utility functions."""

    def test_get_client_ip_from_remote_addr(self, rf):
        """Extract client IP from REMOTE_ADDR."""
        request = rf.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        assert get_client_ip(request) == "192.168.1.1"

    def test_get_client_ip_from_x_forwarded_for(self, rf):
        """Extract client IP from X-Forwarded-For header (proxy)."""
        request = rf.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.5, 198.51.100.2"
        assert get_client_ip(request) == "203.0.113.5"

    def test_get_client_ip_unknown(self, rf):
        """Return 'unknown' when no IP available."""
        request = rf.get("/")
        request.META.pop("REMOTE_ADDR", None)
        assert get_client_ip(request) == "unknown"

    def test_get_identifier_for_authenticated_user(self, rf, django_user_model):
        """Identifier includes user ID for authenticated users."""
        user = django_user_model.objects.create_user(
            username="testuser",
            password="pass",
        )
        request = rf.get("/")
        request.user = user
        identifier = get_identifier_for_user_action(request, "test_action")
        assert f"user:{user.id}" in identifier
        assert "ratelimit:test_action" in identifier

    def test_get_identifier_for_anonymous_user(self, rf):
        """Identifier includes IP for anonymous users."""
        request = rf.get("/")
        request.user = None
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        identifier = get_identifier_for_user_action(request, "test_action")
        assert "ip:192.168.1.1" in identifier
        assert "ratelimit:test_action" in identifier

    def test_is_rate_limited_allows_first_attempt(self, rf, clear_cache):
        """First attempt should not be rate limited."""
        request = rf.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        result = is_rate_limited(
            request,
            "test_action",
            max_attempts=3,
            window_seconds=60,
        )
        assert result is False

    def test_is_rate_limited_allows_within_limit(self, rf, clear_cache):
        """Attempts within limit should not be rate limited."""
        request = rf.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        for _i in range(3):
            result = is_rate_limited(
                request,
                "test_action",
                max_attempts=5,
                window_seconds=60,
            )
            assert result is False

    def test_is_rate_limited_blocks_over_limit(self, rf, clear_cache):
        """Attempts over limit should be rate limited."""
        request = rf.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        for _i in range(3):
            is_rate_limited(request, "test_action", max_attempts=3, window_seconds=60)
        result = is_rate_limited(
            request,
            "test_action",
            max_attempts=3,
            window_seconds=60,
        )
        assert result is True

    def test_is_rate_limited_different_actions(self, rf, clear_cache):
        """Different actions should have separate rate limits."""
        request = rf.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        for _i in range(3):
            is_rate_limited(request, "action_a", max_attempts=3, window_seconds=60)
        # action_b should not be affected
        result = is_rate_limited(request, "action_b", max_attempts=3, window_seconds=60)
        assert result is False

    def test_is_rate_limited_different_users(self, rf, django_user_model, clear_cache):
        """Different users should have separate rate limits."""
        user1 = django_user_model.objects.create_user(username="user1", password="pass")
        user2 = django_user_model.objects.create_user(username="user2", password="pass")

        request1 = rf.get("/")
        request1.user = user1
        for _i in range(3):
            is_rate_limited(request1, "test_action", max_attempts=3, window_seconds=60)

        request2 = rf.get("/")
        request2.user = user2
        result = is_rate_limited(
            request2,
            "test_action",
            max_attempts=3,
            window_seconds=60,
        )
        assert result is False

    def test_get_rate_limit_info(self, rf, clear_cache):
        """Get remaining attempts info."""
        request = rf.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"

        # Make 2 attempts out of 5
        is_rate_limited(request, "test_action", max_attempts=5, window_seconds=60)
        is_rate_limited(request, "test_action", max_attempts=5, window_seconds=60)

        info = get_rate_limit_info(request, "test_action", max_attempts=5)
        assert info["remaining"] == 3


@pytest.mark.django_db
class TestCommentFormRateLimiting:
    """Test rate limiting in comment form."""

    def test_comment_form_accepts_request(self):
        """Comment form should accept request parameter."""
        from django.test import RequestFactory

        from squeaky_knees.blog.forms import CommentForm

        rf = RequestFactory()
        request = rf.get("/")
        request.user = None
        form = CommentForm(request=request)
        assert form.request == request

    def test_comment_form_rate_limit_error(self, django_user_model, clear_cache):
        """Comment form should raise validation error when rate limited."""
        from django.test import RequestFactory

        from squeaky_knees.blog.forms import CommentForm

        user = django_user_model.objects.create_user(
            username="testuser",
            password="pass",
        )
        rf = RequestFactory()

        # Simulate hitting the rate limit
        for i in range(10):
            request = rf.post("/", {"text": f"comment {i}"})
            request.user = user
            is_rate_limited(
                request,
                "comment_add",
                max_attempts=10,
                window_seconds=3600,
            )

        # Next attempt should be rate limited
        request = rf.post("/", {"text": '{"value": "test"}'})
        request.user = user
        form = CommentForm(request.POST, request=request)

        # This should fail with rate limit error
        # Note: clean_text is called during is_valid()
        assert form.is_valid() is False
        assert "too frequently" in str(form.errors).lower()


@pytest.mark.django_db
class TestSignupFormRateLimiting:
    """Test rate limiting in signup form."""

    def test_signup_form_accepts_request(self):
        """Signup form should accept request parameter."""
        from django.test import RequestFactory

        from squeaky_knees.users.forms import UserSignupForm

        rf = RequestFactory()
        request = rf.get("/")
        request.user = None
        form = UserSignupForm(request=request)
        assert form.request == request

    def test_signup_form_rate_limit_error(self, clear_cache):
        """Signup form should raise validation error when rate limited."""
        from django.test import RequestFactory

        from squeaky_knees.users.forms import UserSignupForm

        rf = RequestFactory()

        # Simulate hitting the rate limit
        for i in range(5):
            request = rf.post(
                "/",
                {"username": f"user{i}", "email": f"user{i}@example.com"},
            )
            request.META["REMOTE_ADDR"] = "192.168.1.1"
            request.user = None
            is_rate_limited(request, "user_signup", max_attempts=5, window_seconds=3600)

        # Next attempt should be rate limited
        request = rf.post("/", {"username": "newuser", "email": "newuser@example.com"})
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        request.user = None
        form = UserSignupForm(request.POST, request=request)

        # clean() is called during is_valid()
        assert form.is_valid() is False
        assert "too many signup attempts" in str(form.errors).lower()
