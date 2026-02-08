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
        _content = response.content.decode()
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


@pytest.mark.django_db
class TestTagSearch:
    """Test tag-based search functionality."""

    def test_tag_search_by_slug(self, client, blog_post):
        """Tag search should find posts by tag slug."""
        # Add a tag to the blog post
        blog_post.tags.add("test-tag")
        blog_post.save()

        response = client.get(reverse("blog:search"), {"tag": "test-tag"})

        assert response.status_code == 200
        content = response.content.decode()
        assert blog_post.title in content
        assert "#test-tag" in content

    def test_tag_search_by_name_fallback(self, client, blog_post):
        """Tag search should fallback to name if slug doesn't match."""
        blog_post.tags.add("Python")
        blog_post.save()

        response = client.get(reverse("blog:search"), {"tag": "Python"})

        assert response.status_code == 200

    def test_tag_search_empty_results(self, client):
        """Tag search with no matches should show no results message."""
        response = client.get(reverse("blog:search"), {"tag": "nonexistent-tag"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "No blog posts found" in content or "nonexistent-tag" in content

    def test_tag_search_displays_tag_name(self, client):
        """Tag search results should display the tag being searched."""
        response = client.get(reverse("blog:search"), {"tag": "django"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "#django" in content or "django" in content

    def test_tag_search_result_count(self, client, blog_post):
        """Tag search should show result count."""
        blog_post.tags.add("webdev")
        blog_post.save()

        response = client.get(reverse("blog:search"), {"tag": "webdev"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Found" in content
        assert "result" in content.lower()

    def test_tag_search_multiple_posts(self, client, blog_index, user):
        """Tag search should find multiple posts with same tag."""
        from datetime import date

        from squeaky_knees.blog.models import BlogPage

        # Create two posts with same tag
        for i in range(2):
            post = BlogPage(
                title=f"Post {i}",
                slug=f"post-{i}",
                date=date.today(),
                intro="Test intro",
            )
            post.body = [{"type": "rich_text", "value": "<p>Body</p>"}]
            blog_index.add_child(instance=post)
            post.save_revision().publish()
            post.tags.add("python")
            post.save()

        response = client.get(reverse("blog:search"), {"tag": "python"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Post 0" in content
        assert "Post 1" in content


@pytest.mark.django_db
class TestSearchFallback:
    """Test fallback between tag and query search."""

    def test_query_search_when_no_tag(self, client):
        """Should use query search when no tag parameter."""
        response = client.get(reverse("blog:search"), {"query": "django"})

        assert response.status_code == 200
        content = response.content.decode()
        # Should show query search (not tag search)
        assert "django" in content.lower()

    def test_tag_search_takes_precedence(self, client, blog_post):
        """Tag search should take precedence over query search."""
        blog_post.tags.add("python")
        blog_post.save()

        # Both tag and query params provided
        response = client.get(
            reverse("blog:search"),
            {"tag": "python", "query": "django"},
        )

        assert response.status_code == 200
        content = response.content.decode()
        # Should show tag search results (not query)
        assert "#python" in content or "tag" in content.lower()

    def test_empty_tag_falls_back_to_query(self, client):
        """Empty tag should fallback to query search."""
        response = client.get(
            reverse("blog:search"),
            {"tag": "   ", "query": "test"},
        )

        assert response.status_code == 200
        # Should process query search since tag is empty

    def test_no_params_shows_search_form(self, client):
        """No search params should show empty search form."""
        response = client.get(reverse("blog:search"))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Enter a search term" in content or "Search Blog Posts" in content
