"""Pytest configuration for tests."""

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from wagtail.models import Page
from wagtail.models import Site

from squeaky_knees.blog.models import BlogIndexPage
from squeaky_knees.blog.models import BlogPage

User = get_user_model()


@pytest.fixture(autouse=True)
def mock_recaptcha(monkeypatch):
    """Mock reCAPTCHA validation for tests."""
    # Mock the ReCaptchaField clean method to always pass
    from django_recaptcha.fields import ReCaptchaField

    def mock_clean(self, value):
        # In tests, skip validation and just return the value
        return value

    monkeypatch.setattr(ReCaptchaField, "clean", mock_clean)


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="admin123",
    )


@pytest.fixture
def blog_index(db):
    """Create a blog index page."""
    site = Site.objects.filter(is_default_site=True).first()
    if not site:
        root = Page.objects.first()
        if not root:
            from wagtail.models import Page as WagtailPage

            root = WagtailPage.add_root(title="Root", slug="root")

        site = Site.objects.create(
            hostname="localhost",
            port=80,
            site_name="Test Site",
            root_page=root,
            is_default_site=True,
        )
    else:
        root = site.root_page

    blog_index = BlogIndexPage(
        title="Blog",
        intro="<p>Welcome to the blog</p>",
        slug="blog",
    )
    root.add_child(instance=blog_index)
    blog_index.save_revision().publish()
    return blog_index


@pytest.fixture
def blog_post(db, blog_index, admin_user):
    """Create a blog post."""
    from datetime import date

    blog_post = BlogPage(
        title="Test Blog Post",
        date=date.today(),
        intro="This is a test blog post",
        slug="test-blog-post",
    )
    blog_post.body = [
        {
            "type": "rich_text",
            "value": "<p>This is the body of the test post</p>",
        },
    ]
    blog_index.add_child(instance=blog_post)
    blog_post.save_revision().publish()
    return blog_post


@pytest.fixture
def clear_cache():
    """Clear Django cache before each test."""
    cache.clear()
    yield
    cache.clear()
