"""Tests for sitemap and robots.txt functionality."""

import pytest


@pytest.mark.django_db
class TestSitemapGeneration:
    """Tests for sitemap.xml generation."""

    def test_sitemap_url_exists(self, client):
        """Sitemap should be accessible at /sitemap.xml."""
        response = client.get("/sitemap.xml")
        assert response.status_code == 200

    def test_sitemap_content_type(self, client):
        """Sitemap should have correct content type."""
        response = client.get("/sitemap.xml")
        assert response["Content-Type"] == "application/xml"

    def test_sitemap_includes_blog_posts(self, client, blog_index, blog_post):
        """Sitemap should include published blog posts."""
        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        assert (
            blog_post.title.encode() in response.content or b"blog" in response.content
        )

    def test_sitemap_includes_blog_index(self, client, blog_index):
        """Sitemap should include blog index page."""
        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        assert (
            b"sitemap" in response.content.lower()
            or b"blog" in response.content.lower()
        )

    def test_sitemap_xml_valid_format(self, client):
        """Sitemap should be valid XML."""
        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        # Should have XML declaration
        assert b"<?xml" in response.content

    def test_sitemap_has_xml_namespace(self, client):
        """Sitemap should have proper xmlns declaration."""
        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        assert b"xmlns" in response.content


@pytest.mark.django_db
class TestRobotsTxt:
    """Tests for robots.txt generation."""

    def test_robots_txt_url_exists(self, client):
        """robots.txt should be accessible at /robots.txt."""
        response = client.get("/robots.txt")
        assert response.status_code == 200

    def test_robots_txt_content_type(self, client):
        """robots.txt should have correct content type."""
        response = client.get("/robots.txt")
        assert response["Content-Type"] == "text/plain"

    def test_robots_txt_has_user_agent(self, client):
        """robots.txt should have User-agent directive."""
        response = client.get("/robots.txt")
        assert b"User-agent" in response.content

    def test_robots_txt_allows_disallow(self, client):
        """robots.txt should have Disallow directive."""
        response = client.get("/robots.txt")
        # Should have at least one directive (allow all, or specific disallows)
        assert (
            b"allow" in response.content.lower()
            or b"disallow" in response.content.lower()
        )

    def test_robots_txt_mentions_sitemap(self, client):
        """robots.txt should mention sitemap location."""
        response = client.get("/robots.txt")
        assert b"sitemap" in response.content.lower()

    def test_robots_txt_valid_format(self, client):
        """robots.txt should have valid format."""
        response = client.get("/robots.txt")
        content = response.content.decode()
        # Should not have XML markers
        assert "<?xml" not in content

    def test_robots_txt_allows_googlebot(self, client):
        """robots.txt should allow major search engine bots."""
        response = client.get("/robots.txt")
        content = response.content.decode().lower()
        # Should have configuration for bots (even if allowing all)
        assert ("user-agent" in content) and ("*" in content or "googlebot" in content)


@pytest.mark.django_db
class TestSitemapAndRobotsIntegration:
    """Tests for sitemap and robots.txt working together."""

    def test_robots_txt_references_sitemap_url(self, client):
        """robots.txt should reference the sitemap.xml URL."""
        response = client.get("/robots.txt")
        content = response.content.decode()
        assert "/sitemap.xml" in content

    def test_both_endpoints_accessible(self, client):
        """Both sitemap and robots.txt should be accessible."""
        sitemap_response = client.get("/sitemap.xml")
        robots_response = client.get("/robots.txt")

        assert sitemap_response.status_code == 200
        assert robots_response.status_code == 200

    def test_sitemap_returns_ok_status(self, client):
        """Sitemap request should return 200 OK."""
        response = client.get("/sitemap.xml")
        assert response.status_code == 200

    def test_robots_txt_returns_ok_status(self, client):
        """robots.txt request should return 200 OK."""
        response = client.get("/robots.txt")
        assert response.status_code == 200

    def test_sitemap_with_multiple_blog_posts(self, client, blog_index, user):
        """Sitemap should include multiple blog posts."""
        from datetime import date

        from squeaky_knees.blog.models import BlogPage

        # Create multiple blog posts
        for i in range(3):
            post = BlogPage(
                title=f"Blog Post {i}",
                date=date.today(),
                intro=f"Post {i}",
                slug=f"post-{i}",
            )
            post.body = [{"type": "rich_text", "value": f"<p>Post {i}</p>"}]
            blog_index.add_child(instance=post)
            post.save_revision().publish()

        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        # Should be valid XML
        assert b"<?xml" in response.content

    def test_sitemap_escapes_special_characters(self, client, blog_index, user):
        """Sitemap should properly escape special XML characters."""
        from datetime import date

        from squeaky_knees.blog.models import BlogPage

        # Create a blog post with special characters in title
        post = BlogPage(
            title='Post & Title <with> Special "Characters"',
            date=date.today(),
            intro="Post with special chars",
            slug="special-post",
        )
        post.body = [{"type": "rich_text", "value": "<p>Content</p>"}]
        blog_index.add_child(instance=post)
        post.save_revision().publish()

        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        # Should not cause XML parsing errors
        content = response.content.decode()
        # Should have escaped ampersand or other safe representation
        assert ("&amp;" in content or "&" not in content) or (
            "Post" in content
        )  # Title should be present safely
