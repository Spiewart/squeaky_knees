"""Tests for blog index pagination."""

import pytest
from django.test import RequestFactory

from squeaky_knees.blog.models import BlogIndexPage


@pytest.mark.django_db
class TestBlogIndexPagination:
    """Test blog index page pagination implementation."""

    def test_blog_index_has_posts_per_page_attribute(self):
        """BlogIndexPage should have posts_per_page attribute."""
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        assert hasattr(blog_index, "posts_per_page")
        assert blog_index.posts_per_page == 10

    def test_blog_index_get_context_has_pagination_keys(self):
        """get_context should always include pagination keys."""
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        rf = RequestFactory()
        request = rf.get("/")

        context = blog_index.get_context(request)

        assert "page_obj" in context
        assert "paginator" in context
        assert "is_paginated" in context
        assert "blogpages" in context

    def test_blog_index_get_context_with_page_param(self):
        """get_context should handle page parameter."""
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        rf = RequestFactory()
        request = rf.get("/?page=2")

        context = blog_index.get_context(request)

        # Should not raise an error, even if page doesn't exist
        assert context["page_obj"] is not None

    def test_blog_index_get_context_with_invalid_page(self):
        """get_context should handle invalid page numbers gracefully."""
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        rf = RequestFactory()
        request = rf.get("/?page=invalid")

        # Should not raise, should default to page 1
        context = blog_index.get_context(request)
        assert context["page_obj"].number == 1

    def test_blog_index_get_context_with_large_page_number(self):
        """get_context should handle page numbers beyond range."""
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        rf = RequestFactory()
        request = rf.get("/?page=9999")

        # Should not raise, should default to page 1
        context = blog_index.get_context(request)
        assert context["page_obj"].number == 1

    def test_blog_index_is_not_paginated_with_no_children(self):
        """is_paginated should be False with no blog posts."""
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        rf = RequestFactory()
        request = rf.get("/")

        context = blog_index.get_context(request)

        assert context["is_paginated"] is False

    def test_blog_index_paginator_exists(self):
        """Paginator should be created in context."""
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        rf = RequestFactory()
        request = rf.get("/")

        context = blog_index.get_context(request)
        paginator = context["paginator"]

        assert paginator is not None
        assert hasattr(paginator, "count")
        assert hasattr(paginator, "num_pages")
        assert hasattr(paginator, "page_range")

    def test_blog_index_paginator_count_zero_when_no_posts(self):
        """Paginator count should be 0 with no posts."""
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        rf = RequestFactory()
        request = rf.get("/")

        context = blog_index.get_context(request)
        paginator = context["paginator"]

        assert paginator.count == 0
        assert paginator.num_pages == 1

    def test_blog_index_first_page_by_default(self):
        """First page should be returned by default."""
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        rf = RequestFactory()
        request = rf.get("/")

        context = blog_index.get_context(request)
        page_obj = context["page_obj"]

        assert page_obj.number == 1

    def test_blog_index_blogpages_in_context(self):
        """blogpages should be set to page object list."""
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        rf = RequestFactory()
        request = rf.get("/")

        context = blog_index.get_context(request)

        assert context["blogpages"] == context["page_obj"].object_list

    def test_blog_index_default_page_is_first(self):
        """When page param is missing, should use page 1."""
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        rf = RequestFactory()
        request = rf.get("/")

        context = blog_index.get_context(request)

        assert context["page_obj"].number == 1
