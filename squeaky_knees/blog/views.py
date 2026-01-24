from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect

from .forms import CommentForm
from .models import BlogPage


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
            return redirect(blog_page.url)
    return redirect(blog_page.url)
