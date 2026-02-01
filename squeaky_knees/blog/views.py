from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from config.ratelimit import is_rate_limited

from .email import send_comment_notification
from .forms import CommentForm
from .models import BlogPage, Comment
from .search_forms import BlogSearchForm


@login_required
def add_comment(request, page_id):
    """Handle comment submission for blog posts."""
    blog_page = get_object_or_404(BlogPage, id=page_id)

    if request.method == "POST":
        form = CommentForm(request.POST, request=request)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog_page = blog_page
            comment.author = request.user

            # Handle nested comments (replies to other comments)
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id, blog_page=blog_page)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    pass

            comment.save()
            # Send notification email to blog post owner
            if blog_page.owner:
                send_comment_notification(comment)
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
    query = request.GET.get("query", "").strip()

    if query:
        pending_comments = pending_comments.filter(
            Q(author__username__icontains=query)
            | Q(blog_page__title__icontains=query)
            | Q(text__icontains=query)
        )

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
        "query_string": query,
    }
    return render(request, "blog/moderate_comments.html", context)

# Rate limit search
    if is_rate_limited(request, "blog_search", max_attempts=30, window_seconds=300):
        return render(request, "blog/search_results.html", {
            "error": "Too many search requests. Please wait a moment.",
            "query_string": "",
        })


def search_blog(request):
    """Search blog posts by title, intro, and body content."""
    form = BlogSearchForm()
    results = []
    query_string = ""

    if request.method == "GET" and request.GET.get("query"):
        form = BlogSearchForm(request.GET)
        if form.is_valid():
            query_string = form.cleaned_data["query"]

            # Search using Wagtail's search API
            results = BlogPage.objects.live().search(query_string)

    context = {
        "form": form,
        "results": results,
        "query_string": query_string,
        "result_count": len(results),
    }
    return render(request, "blog/search_results.html", context)
    return render(request, "blog/search_results.html", context)
