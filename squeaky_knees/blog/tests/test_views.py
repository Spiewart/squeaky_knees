import pytest
from django.urls import reverse

from squeaky_knees.blog.models import Comment


@pytest.mark.django_db
class TestBlogViews:
    """Tests for blog views."""

    def test_blog_index_page_loads(self, blog_index, client):
        """Test blog index page loads successfully."""
        response = client.get(blog_index.url)
        assert response.status_code == 200
        assert b"Blog" in response.content

    def test_blog_post_page_loads(self, blog_post, client):
        """Test blog post page loads successfully."""
        response = client.get(blog_post.url)
        assert response.status_code == 200
        assert b"Test Blog Post" in response.content

    def test_add_comment_requires_authentication(self, blog_post, client):
        """Test that adding a comment requires authentication."""
        url = reverse("blog:add_comment", kwargs={"page_id": blog_post.id})
        response = client.post(url, {"text": "Test comment"})
        # Should redirect to login
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_authenticated_user_can_add_comment(self, blog_post, user, client):
        """Test authenticated user can add a comment."""
        client.force_login(user)
        url = reverse("blog:add_comment", kwargs={"page_id": blog_post.id})
        response = client.post(url, {"text": "Test comment"})

        # Should redirect back to blog post
        assert response.status_code == 302

        # Comment should be created but not approved
        comment = Comment.objects.get(blog_page=blog_post, author=user)
        assert comment.text == "Test comment"
        assert not comment.approved

    def test_unapproved_comments_not_visible(self, blog_post, user, client):
        """Test unapproved comments are not visible on the page."""
        # Create unapproved comment
        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text="Unapproved comment",
            approved=False,
        )

        response = client.get(blog_post.url)
        assert response.status_code == 200
        assert b"Unapproved comment" not in response.content

    def test_approved_comments_visible(self, blog_post, user, client):
        """Test approved comments are visible on the page."""
        # Create approved comment
        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text="Approved comment",
            approved=True,
        )

        response = client.get(blog_post.url)
        assert response.status_code == 200
        assert b"Approved comment" in response.content


@pytest.mark.django_db
class TestCommentForm:
    """Tests for comment form."""

    def test_comment_form_visible_for_authenticated_users(
        self, blog_post, user, client
    ):
        """Test comment form is visible for authenticated users."""
        client.force_login(user)
        response = client.get(blog_post.url)
        assert response.status_code == 200
        assert b"Leave a Comment" in response.content
        assert b"Submit Comment" in response.content

    def test_comment_form_not_visible_for_anonymous(self, blog_post, client):
        """Test comment form prompts login for anonymous users."""
        response = client.get(blog_post.url)
        assert response.status_code == 200
        assert b"Log in" in response.content
        assert b"to leave a comment" in response.content
