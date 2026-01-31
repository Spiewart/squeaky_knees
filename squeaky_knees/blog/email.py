"""Email utilities for blog notifications."""

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse


def send_comment_notification(comment):
    """Send email notification when a new comment is submitted.

    Sends to:
    - Blog post author
    - Admin email
    - Comment author (on approval)
    """
    blog_post = comment.blog_page

    # Get blog post author
    author_email = None
    if hasattr(blog_post, 'owner') and blog_post.owner:
        author_email = blog_post.owner.email

    if not author_email:
        # If no post owner, don't send
        return False

    # Create context for email
    context = {
        'blog_post_title': blog_post.title,
        'comment_author': comment.author.username if comment.author else 'Anonymous',
        'comment_text': comment.text,
        'post_url': blog_post.url,
        'admin_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    }

    # Render email subject and body
    subject = f"New comment on: {blog_post.title}"
    html_message = render_to_string('blog/email/comment_notification.html', context)

    # Send email to post author
    try:
        send_mail(
            subject,
            "",  # Plain text version (optional)
            settings.DEFAULT_FROM_EMAIL,
            [author_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception:
        return False


def send_comment_approval_notification(comment):
    """Send email to comment author when their comment is approved.

    Only sends if comment author has an email and is authenticated.
    """
    if not comment.author or not comment.author.email:
        return False

    blog_post = comment.blog_page

    context = {
        'blog_post_title': blog_post.title,
        'author_name': comment.author.username,
        'post_url': blog_post.url,
    }

    subject = f"Your comment on '{blog_post.title}' was approved"
    html_message = render_to_string('blog/email/comment_approved.html', context)

    try:
        send_mail(
            subject,
            "",
            settings.DEFAULT_FROM_EMAIL,
            [comment.author.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception:
        return False
