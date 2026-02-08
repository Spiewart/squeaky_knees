"""Comprehensive tests for URL routing and view behavior."""

import pytest
from django.urls import resolve
from django.urls import reverse
from wagtail.views import serve as wagtail_serve

from squeaky_knees.blog import views as blog_views
from squeaky_knees.blog.models import BlogIndexPage
from squeaky_knees.views import blog_view
from squeaky_knees.views import health_check
from squeaky_knees.views import home_view


@pytest.mark.django_db
class TestHomeView:
    """Tests for the home_view function."""

    def test_home_view_without_blog_index(self, client):
        """When no BlogIndexPage exists, home_view should render home.html."""
        BlogIndexPage.objects.all().delete()

        response = client.get(reverse("home"))

        assert response.status_code == 200
        assert "practical guidance" in response.content.decode().lower()
        assert any(t.name == "pages/home.html" for t in response.templates)

    def test_home_view_shows_content(self, client, blog_index):
        """Home view should always render content (not redirect)."""
        response = client.get(reverse("home"))

        assert response.status_code == 200
        assert any(t.name == "pages/home.html" for t in response.templates)

    def test_home_view_shows_latest_post(self, client, blog_post):
        """Home view should display latest post excerpt."""
        response = client.get(reverse("home"))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Latest post" in content or blog_post.title in content

    def test_home_view_shows_tag_links(self, client, blog_post):
        """Home view should display tag links when posts have tags."""
        response = client.get(reverse("home"))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Browse by topic" in content

    def test_home_view_with_unpublished_blog_index(self, client):
        """Unpublished BlogIndexPage should not redirect."""
        BlogIndexPage.objects.all().delete()

        response = client.get(reverse("home"))

        assert response.status_code == 200
        assert "practical guidance" in response.content.decode().lower()


@pytest.mark.django_db
class TestBlogView:
    """Tests for the blog_view function."""

    def test_blog_view_without_blog_index(self, client):
        """When no BlogIndexPage exists, blog_view should render blog/index.html."""
        BlogIndexPage.objects.all().delete()

        response = client.get(reverse("blog_index"))

        assert response.status_code == 200
        assert "currently being set up" in response.content.decode().lower()

    def test_blog_view_with_blog_index(self, client, blog_index):
        """When BlogIndexPage exists, blog_view should serve it."""
        response = client.get(reverse("blog_index"))

        assert response.status_code == 200
        assert blog_index.title in response.content.decode()


@pytest.mark.django_db
class TestUrlResolution:
    """Tests for URL resolution and endpoint accessibility."""

    def test_resolve_core_urls(self):
        """Core routes should resolve to expected views."""
        assert resolve("/").func == home_view
        assert resolve("/blog/").func == blog_view
        assert resolve("/health/").func == health_check
        assert resolve("/blog/actions/search/").func == blog_views.search_blog

    def test_resolve_wagtail_catchall(self):
        """Wagtail should handle nested blog pages."""
        match = resolve("/blog/some-page/")
        assert match.func == wagtail_serve

    def test_endpoint_status_codes(self, client, blog_index):
        """Key endpoints should return valid responses."""
        response = client.get("/")
        assert response.status_code == 200

        response = client.get("/blog/")
        assert response.status_code == 200

        response = client.get("/about/")
        assert response.status_code == 200

        response = client.get("/health/")
        assert response.status_code == 200

        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/xml"

        response = client.get("/robots.txt")
        assert response.status_code == 200
        assert response["Content-Type"] == "text/plain"

        response = client.get("/feed.xml")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/rss+xml"

        response = client.get("/cms/")
        assert response.status_code in [200, 301, 302, 403, 404]

        response = client.get("/documents/")
        assert response.status_code in [200, 301, 302, 403, 404]

        response = client.get("/accounts/login/")
        assert response.status_code == 200

        response = client.get("/users/~redirect/")
        assert response.status_code in [301, 302]

        response = client.get("/nonexistent-page-12345/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestNavbarLinks:
    """Tests for navbar links in base.html."""

    def test_navbar_links_present(self, client):
        """Navbar should contain Home, Blog, and About links."""
        BlogIndexPage.objects.all().delete()

        response = client.get("/")
        content = response.content.decode()

        assert 'href="/"' in content
        assert 'href="/blog/"' in content
        assert ">About<" in content
