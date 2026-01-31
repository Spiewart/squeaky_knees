import json
from datetime import date

import pytest
from django.urls import reverse

from squeaky_knees.blog.models import BlogPage
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
        response = client.post(
            url,
            {"text": "Test comment"},
        )
        # Should redirect to login
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_authenticated_user_can_add_comment(self, blog_post, user, client):
        """Test authenticated user can add a comment."""
        client.force_login(user)
        url = reverse("blog:add_comment", kwargs={"page_id": blog_post.id})
        response = client.post(
            url,
            {"text": "Test comment"},
        )

        # Should redirect back to blog post
        assert response.status_code == 302

        # Comment should be created but not approved
        comment = Comment.objects.get(blog_page=blog_post, author=user)
        assert len(comment.text) > 0
        assert not comment.approved

    def test_authenticated_user_can_add_json_comment(self, blog_post, user, client):
        """Test authenticated user can add a JSON comment with code block."""
        client.force_login(user)
        url = reverse("blog:add_comment", kwargs={"page_id": blog_post.id})
        payload = json.dumps(
            [
                {"type": "rich_text", "value": "<p>Hello</p>"},
                {
                    "type": "code",
                    "value": {"language": "python", "code": "print('ok')"},
                },
            ],
        )
        response = client.post(url, {"text": payload})
        assert response.status_code == 302

        comment = Comment.objects.get(blog_page=blog_post, author=user)
        assert comment.text[1].block_type == "code"

    def test_unapproved_comments_not_visible(self, blog_post, user, client):
        """Test unapproved comments are not visible on the page."""
        # Create unapproved comment
        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Unapproved comment</p>"}],
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
            text=[{"type": "rich_text", "value": "<p>Approved comment</p>"}],
            approved=True,
        )

        response = client.get(blog_post.url)
        assert response.status_code == 200
        assert b"Approved comment" in response.content

    def test_code_block_comment_renders(self, blog_post, user, client):
        """Test code block comments render with code content."""
        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[
                {
                    "type": "code",
                    "value": {"language": "python", "code": "print('ok')"},
                },
            ],
            approved=True,
        )

        response = client.get(blog_post.url)
        assert response.status_code == 200
        content = response.content
        assert b"language-python" in content
        assert b"print('ok')" in content or b"print(&#x27;ok&#x27;)" in content

    def test_navbar_includes_search_form(self, client):
        """Navbar should include blog search form."""
        response = client.get(reverse("home"))
        assert response.status_code == 200
        content = response.content.decode()
        assert f'action="{reverse("blog:search")}"' in content
        assert 'name="query"' in content


@pytest.mark.django_db
class TestCommentForm:
    """Tests for comment form."""

    def test_comment_form_visible_for_authenticated_users(
        self,
        blog_post,
        user,
        client,
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


@pytest.mark.django_db
class TestModerateCommentsView:
    """Tests for comment moderation view."""

    def test_moderate_comments_requires_staff(self, client, user):
        """Test that moderation page requires staff permissions."""
        client.force_login(user)
        url = reverse("blog:moderate_comments")
        response = client.get(url)
        # Should redirect to login or show forbidden
        assert response.status_code == 302

    def test_staff_can_access_moderation_page(self, client, admin_user):
        """Test that staff users can access moderation page."""
        client.force_login(admin_user)
        url = reverse("blog:moderate_comments")
        response = client.get(url)
        assert response.status_code == 200
        assert b"Moderate Comments" in response.content

    def test_moderation_page_shows_pending_comments(
        self,
        client,
        admin_user,
        blog_post,
        user,
    ):
        """Test moderation page displays pending comments."""
        # Create pending comment
        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Pending comment</p>"}],
            approved=False,
        )

        client.force_login(admin_user)
        url = reverse("blog:moderate_comments")
        response = client.get(url)
        assert response.status_code == 200
        assert b"Pending comment" in response.content

    def test_staff_can_approve_comment(self, client, admin_user, blog_post, user):
        """Test staff can approve a comment."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
            approved=False,
        )

        client.force_login(admin_user)
        url = reverse("blog:moderate_comments")
        response = client.post(
            url,
            {"comment_id": comment.id, "action": "approve"},
        )

        assert response.status_code == 302
        comment.refresh_from_db()
        assert comment.approved

    def test_staff_can_delete_comment(self, client, admin_user, blog_post, user):
        """Test staff can delete a comment."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
            approved=False,
        )

        client.force_login(admin_user)
        url = reverse("blog:moderate_comments")
        response = client.post(
            url,
            {"comment_id": comment.id, "action": "delete"},
        )

        assert response.status_code == 302
        assert not Comment.objects.filter(id=comment.id).exists()

    def test_moderation_page_empty_when_no_pending(self, client, admin_user):
        """Test moderation page shows message when no pending comments."""
        client.force_login(admin_user)
        url = reverse("blog:moderate_comments")
        response = client.get(url)
        assert response.status_code == 200
        assert b"No pending comments" in response.content

    def test_moderation_search_filters_by_author(self, client, admin_user, blog_post, user, django_user_model):
        """Moderation search should filter pending comments by author username."""
        other_user = django_user_model.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="pass123",
        )

        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Alpha pending</p>"}],
            approved=False,
        )
        Comment.objects.create(
            blog_page=blog_post,
            author=other_user,
            text=[{"type": "rich_text", "value": "<p>Bravo pending</p>"}],
            approved=False,
        )

        client.force_login(admin_user)
        url = reverse("blog:moderate_comments")
        response = client.get(url, {"query": "testuser"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "Alpha pending" in content
        assert "Bravo pending" not in content

    def test_moderation_search_filters_by_blog_title(self, client, admin_user, blog_index, blog_post, user):
        """Moderation search should filter pending comments by blog title."""
        second_post = BlogPage(
            title="Second Post",
            date=date.today(),
            intro="Second intro",
            slug="second-post",
        )
        second_post.body = [
            {"type": "rich_text", "value": "<p>Second body</p>"},
        ]
        blog_index.add_child(instance=second_post)
        second_post.save_revision().publish()

        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>First post comment</p>"}],
            approved=False,
        )
        Comment.objects.create(
            blog_page=second_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Second post comment</p>"}],
            approved=False,
        )

        client.force_login(admin_user)
        url = reverse("blog:moderate_comments")
        response = client.get(url, {"query": "Second Post"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "Second post comment" in content
        assert "First post comment" not in content
