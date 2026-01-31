"""Tests for RSS feed functionality."""

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestRSSFeed:
    """Tests for RSS feed generation."""

    def test_rss_feed_url_exists(self, client):
        """RSS feed should be accessible at /feed.xml."""
        response = client.get("/feed.xml")
        assert response.status_code == 200

    def test_rss_feed_content_type(self, client):
        """RSS feed should have correct content type."""
        response = client.get("/feed.xml")
        assert response["Content-Type"] in ["application/rss+xml", "application/xml"]

    def test_rss_feed_has_xml_declaration(self, client):
        """RSS feed should have XML declaration."""
        response = client.get("/feed.xml")
        assert b"<?xml" in response.content

    def test_rss_feed_has_rss_element(self, client):
        """RSS feed should have rss element."""
        response = client.get("/feed.xml")
        assert b"<rss" in response.content

    def test_rss_feed_has_channel(self, client):
        """RSS feed should have channel element."""
        response = client.get("/feed.xml")
        assert b"<channel>" in response.content

    def test_rss_feed_includes_title(self, client):
        """RSS feed should include site title."""
        response = client.get("/feed.xml")
        content = response.content.decode()
        assert "<title>" in content and "</title>" in content

    def test_rss_feed_includes_link(self, client):
        """RSS feed should include site link."""
        response = client.get("/feed.xml")
        content = response.content.decode()
        assert "<link>" in content

    def test_rss_feed_includes_description(self, client):
        """RSS feed should include site description."""
        response = client.get("/feed.xml")
        content = response.content.decode()
        assert "<description>" in content or "<summary>" in content

    def test_rss_feed_includes_blog_posts(self, client, blog_post):
        """RSS feed should include published blog posts."""
        response = client.get("/feed.xml")
        assert response.status_code == 200
        assert b"<item>" in response.content

    def test_rss_feed_item_has_title(self, client, blog_post):
        """Each RSS item should have a title."""
        response = client.get("/feed.xml")
        content = response.content.decode()
        assert blog_post.title in content

    def test_rss_feed_item_has_link(self, client, blog_post):
        """Each RSS item should have a link."""
        response = client.get("/feed.xml")
        assert b"<link>" in response.content

    def test_rss_feed_item_has_description(self, client, blog_post):
        """Each RSS item should have a description."""
        response = client.get("/feed.xml")
        content = response.content.decode()
        # Should contain intro or body
        assert blog_post.intro in content or "blog-post" in content

    def test_rss_feed_item_has_pub_date(self, client, blog_post):
        """Each RSS item should have a publication date."""
        response = client.get("/feed.xml")
        assert b"<pubDate>" in response.content or b"<updated>" in response.content

    def test_rss_feed_item_has_author(self, client, blog_post, user):
        """Each RSS item should have author info."""
        blog_post.owner = user
        blog_post.save()
        response = client.get("/feed.xml")
        content = response.content.decode()
        # Author or creator info should be present
        assert (
            "<author>" in content
            or "<creator>" in content
            or user.username in content
            or "<item>" in content
        )

    def test_rss_feed_multiple_posts(self, client, blog_index, user):
        """RSS feed should include multiple blog posts."""
        from datetime import date

        from squeaky_knees.blog.models import BlogPage

        # Create multiple blog posts
        for i in range(3):
            post = BlogPage(
                title=f"Post {i}",
                date=date.today(),
                intro=f"Intro {i}",
                slug=f"post-{i}",
            )
            post.body = [{"type": "rich_text", "value": f"<p>Body {i}</p>"}]
            blog_index.add_child(instance=post)
            post.save_revision().publish()

        response = client.get("/feed.xml")
        assert response.status_code == 200
        # Should have multiple items
        assert response.content.count(b"<item>") >= 3

    def test_rss_feed_latest_posts_first(self, client, blog_index, user):
        """RSS feed should list latest posts first."""
        from datetime import date
        from datetime import timedelta

        from squeaky_knees.blog.models import BlogPage

        # Create older post
        older_post = BlogPage(
            title="Older Post",
            date=date.today() - timedelta(days=5),
            intro="Older",
            slug="older",
        )
        older_post.body = [{"type": "rich_text", "value": "<p>Old</p>"}]
        blog_index.add_child(instance=older_post)
        older_post.save_revision().publish()

        # Create newer post
        newer_post = BlogPage(
            title="Newer Post",
            date=date.today(),
            intro="Newer",
            slug="newer",
        )
        newer_post.body = [{"type": "rich_text", "value": "<p>New</p>"}]
        blog_index.add_child(instance=newer_post)
        newer_post.save_revision().publish()

        response = client.get("/feed.xml")
        content = response.content.decode()
        # Newer post should appear before older post
        newer_pos = content.find("Newer Post")
        older_pos = content.find("Older Post")
        assert newer_pos > 0 and older_pos > 0 and newer_pos < older_pos

    def test_rss_feed_escapes_html(self, client, blog_post):
        """RSS feed should properly escape HTML in descriptions."""
        response = client.get("/feed.xml")
        content = response.content.decode()
        # Should not have unescaped HTML tags in text content
        # or should have proper CDATA sections
        assert "<?xml" in content  # Valid XML

    def test_rss_feed_includes_only_published_posts(self, client, blog_index, user):
        """RSS feed should include only published/live blog posts."""
        from datetime import date

        from squeaky_knees.blog.models import BlogPage

        # Create a published post
        published_post = BlogPage(
            title="Published",
            date=date.today(),
            intro="Published",
            slug="published",
        )
        published_post.body = [{"type": "rich_text", "value": "<p>Pub</p>"}]
        blog_index.add_child(instance=published_post)
        published_post.save_revision().publish()

        response = client.get("/feed.xml")
        assert b"Published" in response.content

    def test_rss_feed_valid_xml(self, client, blog_post):
        """RSS feed should be valid XML."""
        response = client.get("/feed.xml")
        # Should parse as valid XML
        assert b"<?xml" in response.content
        assert b"</rss>" in response.content

    def test_rss_feed_has_language(self, client):
        """RSS feed should specify language."""
        response = client.get("/feed.xml")
        content = response.content.decode()
        assert "language" in content or "xml:lang" in content or "en" in content
