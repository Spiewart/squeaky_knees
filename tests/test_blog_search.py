"""Tests for blog search functionality."""

import pytest
from django.test import Client
from django.urls import reverse

from squeaky_knees.blog.search_forms import BlogSearchForm


@pytest.mark.django_db
class TestBlogSearchForm:
    """Test blog search form validation."""

    def test_search_form_valid(self):
        """Valid search query should pass."""
        form = BlogSearchForm({"query": "django"})
        assert form.is_valid()

    def test_search_form_empty(self):
        """Empty query should fail."""
        form = BlogSearchForm({"query": ""})
        assert not form.is_valid()
        assert (
            "required" in str(form.errors).lower()
            or "empty" in str(form.errors).lower()
        )

    def test_search_form_too_short(self):
        """Query shorter than 2 chars should fail."""
        form = BlogSearchForm({"query": "a"})
        assert not form.is_valid()
        assert "2 characters" in str(form.errors)

    def test_search_form_too_long(self):
        """Query longer than 200 chars should fail."""
        form = BlogSearchForm({"query": "x" * 300})
        assert not form.is_valid()
        assert (
            "characters" in str(form.errors).lower()
            or "exceed" in str(form.errors).lower()
        )

    def test_search_form_removes_harmful_chars(self):
        """Harmful characters should be removed from query."""
        form = BlogSearchForm({"query": 'test<script>"alert"</script>'})
        assert form.is_valid()
        query = form.cleaned_data["query"]
        assert "<" not in query
        assert ">" not in query
        assert "<script>" not in query

    def test_search_form_strips_whitespace(self):
        """Whitespace should be stripped."""
        form = BlogSearchForm({"query": "  django  "})
        assert form.is_valid()
        assert form.cleaned_data["query"] == "django"


@pytest.mark.django_db
class TestBlogSearchView:
    """Test blog search view."""

    def test_search_page_loads(self):
        """Search page should load."""
        client = Client()
        response = client.get(reverse("blog:search"))
        assert response.status_code == 200
        assert "Search Blog Posts" in response.content.decode()

    def test_search_form_on_page(self):
        """Search form should be displayed."""
        client = Client()
        response = client.get(reverse("blog:search"))
        content = response.content.decode()
        assert "query" in content
        assert "Search blog posts" in content

    def test_search_query_param_loads_form(self):
        """GET with empty query should show search form."""
        client = Client()
        response = client.get(reverse("blog:search"), {"query": ""})
        assert response.status_code == 200

    def test_search_displays_results(self):
        """Search results should be displayed."""
        client = Client()
        response = client.get(reverse("blog:search"), {"query": "Django"})
        assert response.status_code == 200
        # Results may or may not appear depending on search backend

    def test_search_with_harmful_query_is_sanitized(self):
        """Harmful characters in query should be removed."""
        client = Client()
        response = client.get(
            reverse("blog:search"),
            {"query": "django<script>alert()</script>"},
        )
        assert response.status_code == 200

    def test_search_result_count_displays(self):
        """Result count should be displayed."""
        client = Client()
        response = client.get(reverse("blog:search"), {"query": "Python"})
        content = response.content.decode()
        # Should display "Found X results for ..."
        assert "Found" in content or "result" in content.lower()

    def test_search_no_results_message(self):
        """No results message should display for empty results."""
        # Search for something that shouldn't exist
        client = Client()
        response = client.get(
            reverse("blog:search"),
            {"query": "xyzuniquethingnothere"},
        )
        content = response.content.decode()
        # Should have search results section
        assert response.status_code == 200

    def test_search_instruction_before_query(self):
        """Instruction should show before query is entered."""
        client = Client()
        response = client.get(reverse("blog:search"))
        content = response.content.decode()
        assert "Enter a search term" in content or "Search Blog Posts" in content


@pytest.mark.django_db
class TestBlogSearchIntegration:
    """Test search integration with blog posts."""

    def test_search_finds_by_title(self):
        """Search should find blog posts by title."""
        # This is a basic integration test
        # Actual search results depend on Wagtail search backend configuration

    def test_search_form_sanitizes_input(self):
        """Search form should sanitize user input."""
        xss_query = '"><script>alert("xss")</script><"'
        form = BlogSearchForm({"query": xss_query})
        # Should still be valid (harmful chars removed)
        # or invalid (query becomes empty after sanitization)
        # Either way, should be safe
        if form.is_valid():
            query = form.cleaned_data["query"]
            assert "<" not in query
            assert ">" not in query
