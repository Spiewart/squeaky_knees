"""Tests for blog email notifications."""

import pytest
from django.conf import settings
from django.core import mail

from squeaky_knees.blog.email import send_comment_approval_notification
from squeaky_knees.blog.email import send_comment_notification
from squeaky_knees.blog.models import Comment


@pytest.mark.django_db
class TestCommentNotificationEmails:
    """Tests for comment notification emails."""

    def test_send_comment_notification_returns_true_on_success(self, blog_post, user):
        """send_comment_notification should return True when successful."""
        # Set post owner
        blog_post.owner = user
        blog_post.save()

        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []  # Clear outbox
        result = send_comment_notification(comment)

        assert result is True
        assert len(mail.outbox) == 1

    def test_send_comment_notification_returns_false_without_author_email(
        self,
        blog_post,
        user,
    ):
        """send_comment_notification should return False if post has no owner."""
        # Don't set post owner
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        result = send_comment_notification(comment)

        assert result is False
        assert len(mail.outbox) == 0

    def test_send_comment_notification_includes_blog_post_title(
        self,
        blog_post,
        user,
    ):
        """Email subject should include blog post title."""
        blog_post.owner = user
        blog_post.save()

        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_notification(comment)

        assert len(mail.outbox) == 1
        assert blog_post.title in mail.outbox[0].subject

    def test_send_comment_notification_email_to_post_owner(self, blog_post, user):
        """Email should be sent to blog post owner."""
        blog_post.owner = user
        blog_post.save()

        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_notification(comment)

        assert len(mail.outbox) == 1
        assert user.email in mail.outbox[0].to

    def test_send_comment_notification_includes_comment_author(self, blog_post, user):
        """Email body should include comment author name."""
        blog_post.owner = user
        blog_post.save()

        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_notification(comment)

        assert len(mail.outbox) == 1
        email_content = mail.outbox[0].body or mail.outbox[0].alternatives[0][0]
        assert user.username in email_content

    def test_send_comment_notification_includes_post_url(self, blog_post, user):
        """Email should include link to blog post."""
        blog_post.owner = user
        blog_post.save()

        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_notification(comment)

        assert len(mail.outbox) == 1
        email_content = mail.outbox[0].body or mail.outbox[0].alternatives[0][0]
        assert "blog" in email_content.lower()

    def test_send_comment_notification_sends_html_email(self, blog_post, user):
        """Email should have HTML version."""
        blog_post.owner = user
        blog_post.save()

        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_notification(comment)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].alternatives  # Has HTML alternative

    def test_send_comment_notification_handles_exception(self, blog_post, user):
        """send_comment_notification should return False on email error."""
        blog_post.owner = user
        blog_post.save()

        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        # Mock send_mail to raise an exception
        import squeaky_knees.blog.email as email_module

        original_send_mail = email_module.send_mail

        class EmailServiceError(OSError):
            """Custom exception for email service errors."""

        def mock_send_mail(*args, **kwargs):
            error_msg = "Email service error"
            raise EmailServiceError(error_msg)

        email_module.send_mail = mock_send_mail
        try:
            result = send_comment_notification(comment)
            assert result is False
        finally:
            email_module.send_mail = original_send_mail

    def test_send_comment_notification_with_code_block(self, blog_post, user):
        """Email should handle comments with code blocks."""
        blog_post.owner = user
        blog_post.save()

        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[
                {
                    "type": "code",
                    "value": {"code": "print('hello')", "language": "python"},
                },
            ],
        )

        mail.outbox = []
        result = send_comment_notification(comment)

        assert result is True
        assert len(mail.outbox) == 1


@pytest.mark.django_db
class TestCommentApprovalEmails:
    """Tests for comment approval notification emails."""

    def test_send_comment_approval_notification_returns_true(self, blog_post, user):
        """send_comment_approval_notification should return True on success."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        result = send_comment_approval_notification(comment)

        assert result is True
        assert len(mail.outbox) == 1

    def test_send_comment_approval_notification_returns_false_without_email(
        self,
        blog_post,
        user,
    ):
        """Return False if comment author has no email."""
        user.email = ""
        user.save()

        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Comment</p>"}],
        )

        mail.outbox = []
        result = send_comment_approval_notification(comment)

        assert result is False
        assert len(mail.outbox) == 0

    def test_send_comment_approval_notification_email_to_author(
        self,
        blog_post,
        user,
    ):
        """Email should be sent to comment author."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_approval_notification(comment)

        assert len(mail.outbox) == 1
        assert user.email in mail.outbox[0].to

    def test_send_comment_approval_notification_includes_author_name(
        self,
        blog_post,
        user,
    ):
        """Email body should include author name."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_approval_notification(comment)

        assert len(mail.outbox) == 1
        email_content = mail.outbox[0].body or mail.outbox[0].alternatives[0][0]
        assert user.username in email_content

    def test_send_comment_approval_notification_includes_post_title(
        self,
        blog_post,
        user,
    ):
        """Email subject should include blog post title."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_approval_notification(comment)

        assert len(mail.outbox) == 1
        assert blog_post.title in mail.outbox[0].subject

    def test_send_comment_approval_notification_subject_mentions_approval(
        self,
        blog_post,
        user,
    ):
        """Email subject should mention approval."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_approval_notification(comment)

        assert len(mail.outbox) == 1
        assert "approved" in mail.outbox[0].subject.lower()

    def test_send_comment_approval_notification_is_html(self, blog_post, user):
        """Email should have HTML version."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_approval_notification(comment)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].alternatives

    def test_send_comment_approval_notification_includes_post_url(
        self,
        blog_post,
        user,
    ):
        """Email should include link to the blog post."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_approval_notification(comment)

        assert len(mail.outbox) == 1
        email_content = mail.outbox[0].body or mail.outbox[0].alternatives[0][0]
        assert "blog" in email_content.lower()

    def test_send_comment_approval_notification_handles_exception(
        self,
        blog_post,
        user,
    ):
        """send_comment_approval_notification should return False on error."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        import squeaky_knees.blog.email as email_module

        original_send_mail = email_module.send_mail

        class EmailServiceError(OSError):
            """Custom exception for email service errors."""

        def mock_send_mail(*args, **kwargs):
            error_msg = "Email service error"
            raise EmailServiceError(error_msg)

        email_module.send_mail = mock_send_mail
        try:
            result = send_comment_approval_notification(comment)
            assert result is False
        finally:
            email_module.send_mail = original_send_mail

    def test_send_comment_approval_notification_from_default_email(
        self,
        blog_post,
        user,
    ):
        """Email should be from DEFAULT_FROM_EMAIL."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )

        mail.outbox = []
        send_comment_approval_notification(comment)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL
