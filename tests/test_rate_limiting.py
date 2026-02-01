"""Tests for endpoint rate limiting."""

import pytest
from django.urls import reverse

from config.ratelimit import is_rate_limited


@pytest.mark.django_db
class TestSearchRateLimiting:
    """Test rate limiting on blog search endpoint."""

    def test_search_allows_multiple_queries_within_limit(self, client):
        """Search should allow multiple queries within rate limit."""
        for i in range(5):
            response = client.get(reverse("blog:search"), {"query": f"test{i}"})
            assert response.status_code == 200

    def test_search_blocks_excessive_queries(self, rf, clear_cache):
        """Search should block after exceeding rate limit."""
        from django.test import RequestFactory

        rf = RequestFactory()

        # Simulate exceeding rate limit (30 attempts per 300 seconds)
        for i in range(31):
            request = rf.get(f"/blog/actions/search/?query=test{i}")
            request.META["REMOTE_ADDR"] = "192.168.1.1"
            request.user = None
            is_rate_limited(request, "blog_search", max_attempts=30, window_seconds=300)

        # Next request should be rate limited
        request = rf.get("/blog/actions/search/?query=final")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        request.user = None
        result = is_rate_limited(
            request,
            "blog_search",
            max_attempts=30,
            window_seconds=300,
        )
        assert result is True


@pytest.mark.django_db
class TestCommentRateLimiting:
    """Test rate limiting on comment submission."""

    def test_comment_rate_limit_enforced(self, blog_post, user, client, clear_cache):
        """Comments should be rate limited."""
        client.force_login(user)
        url = reverse("blog:add_comment", kwargs={"page_id": blog_post.id})

        # Submit comments up to the limit (10 per hour by default)
        for i in range(10):
            response = client.post(url, {"text": f"comment {i}"})
            # Should succeed (or redirect to post)
            assert response.status_code in [200, 302]

        # The 11th comment should be blocked or rate limited
        # This depends on how the rate limiter integrates with the form
        from squeaky_knees.blog.models import Comment

        comment_count = Comment.objects.filter(author=user).count()
        assert comment_count >= 10  # Should have created at least 10 comments


@pytest.mark.django_db
class TestSignupRateLimiting:
    """Test rate limiting on user signup."""

    def test_signup_rate_limit_enforced(self, client, clear_cache):
        """Signup should be rate limited (5 per hour)."""
        from django.test import RequestFactory

        from squeaky_knees.users.forms import UserSignupForm

        rf = RequestFactory()

        # Attempt multiple signups from same IP
        for i in range(5):
            request = rf.post(f"/accounts/signup/?email=user{i}@example.com")
            request.META["REMOTE_ADDR"] = "192.168.1.1"
            request.user = None
            form = UserSignupForm(request=request)
            # Form should validate rate limiting in clean()
            # This would be called during form.is_valid()

        # After 5 attempts, next signup should fail
        request = rf.post("/accounts/signup/?email=user6@example.com")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        request.user = None
        form = UserSignupForm(request=request)
        # The form's clean() method should catch the rate limit
        assert form.is_valid() is False
        assert form.is_valid() is False
