from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from .forms import CommentForm
from .models import BlogPage
from .models import Comment


@login_required
def add_comment(request, page_id):
    """Handle comment submission for blog posts."""
    blog_page = get_object_or_404(BlogPage, id=page_id)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog_page = blog_page
            comment.author = request.user
            comment.save()
            messages.success(
                request,
                "Your comment has been submitted and is awaiting moderation.",
            )
        else:
            # Log form errors for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Comment form errors: {form.errors}")
            messages.error(
                request,
                "Comment submission failed. Please try again.",
            )
    return redirect(blog_page.url)


def is_moderator(user):
    """Check if user is a staff member or moderator."""
    return user.is_staff


@user_passes_test(is_moderator)
def moderate_comments(request):
    """View to moderate pending comments."""
    pending_comments = Comment.objects.filter(approved=False).order_by("-created")

    if request.method == "POST":
        comment_id = request.POST.get("comment_id")
        action = request.POST.get("action")

        try:
            comment = Comment.objects.get(id=comment_id)
            if action == "approve":
                comment.approved = True
                comment.save()
                messages.success(request, f"Comment approved.")
            elif action == "delete":
                comment.delete()
                messages.success(request, f"Comment deleted.")
        except Comment.DoesNotExist:
            messages.error(request, "Comment not found.")

        return redirect("blog:moderate_comments")

    context = {
        "pending_comments": pending_comments,
    }
    return render(request, "blog/moderate_comments.html", context)
