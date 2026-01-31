"""Tests for nested comments feature."""

import pytest
from django.test import RequestFactory

from squeaky_knees.blog.models import Comment


@pytest.mark.django_db
class TestNestedComments:
    """Tests for comment nesting/replies."""

    def test_comment_can_have_parent(self, blog_post, user):
        """Comment should support parent_comment field."""
        parent_comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent comment</p>"}],
        )

        reply_comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent_comment,
            text=[{"type": "rich_text", "value": "<p>Reply comment</p>"}],
        )

        assert reply_comment.parent == parent_comment
        assert reply_comment.is_reply() is True

    def test_top_level_comment_has_no_parent(self, blog_post, user):
        """Top-level comments should have no parent."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Top-level comment</p>"}],
        )

        assert comment.parent is None
        assert comment.is_reply() is False

    def test_get_depth_for_top_level_comment(self, blog_post, user):
        """Top-level comment depth should be 0."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Comment</p>"}],
        )

        assert comment.get_depth() == 0

    def test_get_depth_for_first_level_reply(self, blog_post, user):
        """Direct reply depth should be 1."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
        )

        reply = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply</p>"}],
        )

        assert reply.get_depth() == 1

    def test_get_depth_for_nested_replies(self, blog_post, user):
        """Nested reply depth should increase correctly."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
        )

        reply1 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply 1</p>"}],
        )

        reply2 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=reply1,
            text=[{"type": "rich_text", "value": "<p>Reply 2</p>"}],
        )

        reply3 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=reply2,
            text=[{"type": "rich_text", "value": "<p>Reply 3</p>"}],
        )

        assert reply1.get_depth() == 1
        assert reply2.get_depth() == 2
        assert reply3.get_depth() == 3

    def test_get_root_comment_for_top_level(self, blog_post, user):
        """Root of top-level comment should be itself."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Comment</p>"}],
        )

        assert comment.get_root_comment() == comment

    def test_get_root_comment_for_nested_reply(self, blog_post, user):
        """Root should be the original comment."""
        root = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Root</p>"}],
        )

        reply1 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=root,
            text=[{"type": "rich_text", "value": "<p>Reply 1</p>"}],
        )

        reply2 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=reply1,
            text=[{"type": "rich_text", "value": "<p>Reply 2</p>"}],
        )

        assert reply2.get_root_comment() == root

    def test_get_all_replies_direct_replies(self, blog_post, user):
        """get_all_replies should return direct replies."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
            approved=True,
        )

        reply1 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply 1</p>"}],
            approved=True,
        )

        reply2 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply 2</p>"}],
            approved=True,
        )

        replies = parent.get_all_replies()
        assert len(replies) == 2
        assert reply1 in replies
        assert reply2 in replies

    def test_get_all_replies_nested_replies(self, blog_post, user):
        """get_all_replies should return nested replies recursively."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
            approved=True,
        )

        reply1 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply 1</p>"}],
            approved=True,
        )

        reply2 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=reply1,
            text=[{"type": "rich_text", "value": "<p>Reply 2</p>"}],
            approved=True,
        )

        replies = parent.get_all_replies()
        assert len(replies) == 2
        assert reply1 in replies
        assert reply2 in replies

    def test_get_all_replies_only_approved(self, blog_post, user):
        """get_all_replies should only return approved replies by default."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
            approved=True,
        )

        approved_reply = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Approved</p>"}],
            approved=True,
        )

        unapproved_reply = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Unapproved</p>"}],
            approved=False,
        )

        replies = parent.get_all_replies()
        assert len(replies) == 1
        assert approved_reply in replies
        assert unapproved_reply not in replies

    def test_get_all_replies_includes_unapproved_when_requested(
        self, blog_post, user
    ):
        """get_all_replies should include unapproved when requested."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
            approved=True,
        )

        unapproved_reply = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Unapproved</p>"}],
            approved=False,
        )

        replies = parent.get_all_replies(approved_only=False)
        assert len(replies) == 1
        assert unapproved_reply in replies

    def test_top_level_comments_not_included_in_replies(self, blog_post, user):
        """Top-level comments should not be included in replies."""
        comment1 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Comment 1</p>"}],
            approved=True,
        )

        comment2 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Comment 2</p>"}],
            approved=True,
        )

        assert comment2 not in comment1.get_all_replies()

    def test_reply_deletion_cascades(self, blog_post, user):
        """Deleting a reply should cascade delete its replies."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
        )

        reply = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply</p>"}],
        )

        nested_reply = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=reply,
            text=[{"type": "rich_text", "value": "<p>Nested</p>"}],
        )

        reply_id = reply.id
        nested_id = nested_reply.id

        reply.delete()

        assert not Comment.objects.filter(id=reply_id).exists()
        assert not Comment.objects.filter(id=nested_id).exists()

    def test_parent_comment_deletion_cascades(self, blog_post, user):
        """Deleting a parent comment should cascade delete its replies."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
        )

        reply = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply</p>"}],
        )

        parent_id = parent.id
        reply_id = reply.id

        parent.delete()

        assert not Comment.objects.filter(id=parent_id).exists()
        assert not Comment.objects.filter(id=reply_id).exists()

    def test_can_create_self_referential_comment_in_model(self, blog_post, user):
        """Django allows self-referential but validation should prevent it."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Comment</p>"}],
        )

        # Django allows this at model level but it's a logical error
        comment.parent = comment
        comment.save()

        # Reload to verify
        reloaded = Comment.objects.get(id=comment.id)
        assert reloaded.parent_id == reloaded.id

    def test_multiple_replies_to_same_comment(self, blog_post, user):
        """Multiple comments can reply to the same parent."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
        )

        reply1 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply 1</p>"}],
        )

        reply2 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply 2</p>"}],
        )

        reply3 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply 3</p>"}],
        )

        assert parent.replies.count() == 3
        assert reply1.parent == parent
        assert reply2.parent == parent
        assert reply3.parent == parent

    def test_reply_belongs_to_same_blog_post(self, blog_post, user):
        """Reply should belong to the same blog post as parent."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
        )

        reply = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply</p>"}],
        )

        assert reply.blog_page == parent.blog_page

    def test_str_representation_for_reply(self, blog_post, user):
        """String representation should work for replies too."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
        )

        reply = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply</p>"}],
        )

        assert str(reply) == f"Comment by {user.username} on {blog_post.title}"

    def test_replies_queryset_filtering(self, blog_post, user):
        """Can filter replies by approval status."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
        )

        approved = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Approved</p>"}],
            approved=True,
        )

        unapproved = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Unapproved</p>"}],
            approved=False,
        )

        approved_replies = parent.replies.filter(approved=True)
        assert approved in approved_replies
        assert unapproved not in approved_replies

@pytest.mark.django_db
class TestNestedCommentsTemplateRendering:
    """Tests for nested comments template rendering."""

    def test_blog_page_context_includes_only_top_level_comments(
        self, client, blog_post, user
    ):
        """Blog page context should include only top-level comments."""
        # Create top-level comment
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
            approved=True,
        )

        # Create nested reply
        reply = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Reply</p>"}],
            approved=True,
        )

        # Get blog page context
        response = client.get(blog_post.url)
        assert response.status_code == 200
        context = response.context

        # Only top-level comment should be in context
        comments = context.get("comments")
        assert comments is not None
        assert parent in comments
        assert reply not in comments

    def test_nested_comments_render_in_template(self, client, blog_post, user):
        """Nested comments should render correctly in template."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent comment</p>"}],
            approved=True,
        )

        reply = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>This is a reply</p>"}],
            approved=True,
        )

        response = client.get(blog_post.url)
        content = response.content.decode()

        # Check that both comments are rendered
        assert "Parent comment" in content
        assert "This is a reply" in content
        # Check for reply badge
        assert "Reply" in content or "reply" in content.lower()

    def test_deeply_nested_comments_render(self, client, blog_post, user):
        """Multiple levels of nested comments should render correctly."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Level 0</p>"}],
            approved=True,
        )

        level1 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=parent,
            text=[{"type": "rich_text", "value": "<p>Level 1</p>"}],
            approved=True,
        )

        level2 = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            parent=level1,
            text=[{"type": "rich_text", "value": "<p>Level 2</p>"}],
            approved=True,
        )

        response = client.get(blog_post.url)
        content = response.content.decode()

        # All levels should be rendered
        assert "Level 0" in content
        assert "Level 1" in content
        assert "Level 2" in content

    def test_reply_form_includes_code_block_option(self, client, blog_post, user):
        """Reply form should include option to add code blocks."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
            approved=True,
        )

        # Login as user
        client.force_login(user)
        response = client.get(blog_post.url)
        content = response.content.decode()

        # Check for code block button
        assert "Add Code" in content or "add.*code" in content.lower()
        assert "Add Text" in content or "add.*text" in content.lower()
        # Check for remove control
        assert "Remove" in content

    def test_nested_reply_form_structure(self, client, blog_post, user):
        """Reply form should have correct structure for multiple blocks."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
            approved=True,
        )

        client.force_login(user)
        response = client.get(blog_post.url)
        content = response.content.decode()

        # Check for reply-to form container
        assert f'id="reply-to-{parent.id}"' in content
        assert f'data-comment-id="{parent.id}"' in content


@pytest.mark.django_db
class TestNestedCommentSubmission:
    """Tests for submitting nested comments through the form."""

    def test_submit_reply_with_text_only(self, client, blog_post, user):
        """Should be able to submit a reply with text only."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
            approved=False,
        )

        client.force_login(user)
        response = client.post(
            f"/blog/actions/comment/{blog_post.id}/",
            {
                "parent_id": parent.id,
                "text": '[{"type":"rich_text","value":"<p>Reply text</p>"}]',
                "captcha": "test_token",
            },
        )

        # Should redirect after submission
        assert response.status_code == 302

        # Reply should be created
        reply = Comment.objects.filter(parent=parent).first()
        assert reply is not None
        assert reply.author == user
        assert reply.blog_page == blog_post
        assert reply.parent == parent

    def test_submit_reply_with_code_block(self, client, blog_post, user):
        """Should be able to submit a reply with code block."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
            approved=False,
        )

        client.force_login(user)
        response = client.post(
            f"/blog/actions/comment/{blog_post.id}/",
            {
                "parent_id": parent.id,
                "text": '[{"type":"code","value":{"language":"python","content":"print(hello)"}}]',
                "captcha": "test_token",
            },
        )

        # Should redirect after submission
        assert response.status_code == 302

        # Reply with code should be created
        reply = Comment.objects.filter(parent=parent).first()
        assert reply is not None
        assert reply.parent == parent

    def test_submit_reply_with_multiple_blocks(self, client, blog_post, user):
        """Should be able to submit a reply with multiple content blocks."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Parent</p>"}],
            approved=False,
        )

        client.force_login(user)
        response = client.post(
            f"/blog/actions/comment/{blog_post.id}/",
            {
                "parent_id": parent.id,
                "text": '[{"type":"rich_text","value":"<p>Text</p>"},{"type":"code","value":{"language":"python","content":"x=1"}}]',
                "captcha": "test_token",
            },
        )

        # Should redirect after submission
        assert response.status_code == 302

        # Reply with multiple blocks should be created
        reply = Comment.objects.filter(parent=parent).first()
        assert reply is not None
        assert reply.parent == parent

    def test_reply_to_reply_creates_correct_hierarchy(self, client, blog_post, user):
        """Reply to a reply should create correct parent-child hierarchy."""
        parent = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Level 0</p>"}],
            approved=False,
        )

        # First reply
        client.force_login(user)
        client.post(
            f"/blog/actions/comment/{blog_post.id}/",
            {
                "parent_id": parent.id,
                "text": '[{"type":"rich_text","value":"<p>Level 1</p>"}]',
                "captcha": "test_token",
            },
        )

        level1 = Comment.objects.filter(parent=parent).first()
        assert level1 is not None

        # Second reply (reply to the reply)
        client.post(
            f"/blog/actions/comment/{blog_post.id}/",
            {
                "parent_id": level1.id,
                "text": '[{"type":"rich_text","value":"<p>Level 2</p>"}]',
                "captcha": "test_token",
            },
        )

        level2 = Comment.objects.filter(parent=level1).first()
        assert level2 is not None
        assert level2.parent == level1
        assert level2.get_depth() == 2
