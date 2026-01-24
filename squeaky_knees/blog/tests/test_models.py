import pytest
from django.test import Client

from squeaky_knees.blog.models import Comment


@pytest.mark.django_db
class TestBlogModels:
    """Tests for blog models."""

    def test_blog_index_page_creation(self, blog_index):
        """Test blog index page is created."""
        assert blog_index.title == "Blog"
        assert blog_index.live

    def test_blog_page_creation(self, blog_post):
        """Test blog page is created."""
        assert blog_post.title == "Test Blog Post"
        assert blog_post.intro == "This is a test blog post"
        assert blog_post.live

    def test_blog_page_get_context(self, blog_post, client):
        """Test blog page context includes comments."""
        context = blog_post.get_context({})
        assert "comments" in context
        assert "comment_form" in context


@pytest.mark.django_db
class TestCommentModel:
    """Tests for comment model."""

    def test_comment_creation(self, blog_post, user):
        """Test comment creation."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text="Test comment",
        )
        assert comment.blog_page == blog_post
        assert comment.author == user
        assert comment.text == "Test comment"
        assert not comment.approved  # Should not be approved by default

    def test_comment_str(self, blog_post, user):
        """Test comment string representation."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text="Test comment",
        )
        expected = f"Comment by {user.username} on {blog_post.title}"
        assert str(comment) == expected

    def test_approved_comments_filter(self, blog_post, user):
        """Test filtering approved comments."""
        # Create approved comment
        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text="Approved comment",
            approved=True,
        )
        # Create unapproved comment
        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text="Unapproved comment",
            approved=False,
        )

        approved_comments = blog_post.comments.filter(approved=True)
        assert approved_comments.count() == 1
        assert approved_comments.first().text == "Approved comment"
