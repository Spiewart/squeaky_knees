from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for comment moderation."""

    list_display = ["author", "blog_page", "text_preview", "created", "approved"]
    list_filter = ["approved", "created"]
    search_fields = ["author__username", "text", "blog_page__title"]
    actions = ["approve_comments", "unapprove_comments"]
    readonly_fields = ["created"]

    def text_preview(self, obj):
        """Show a preview of the comment text."""
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    text_preview.short_description = "Comment"

    def approve_comments(self, request, queryset):
        """Approve selected comments."""
        updated = queryset.update(approved=True)
        self.message_user(request, f"{updated} comment(s) approved.")

    approve_comments.short_description = "Approve selected comments"

    def unapprove_comments(self, request, queryset):
        """Unapprove selected comments."""
        updated = queryset.update(approved=False)
        self.message_user(request, f"{updated} comment(s) unapproved.")

    unapprove_comments.short_description = "Unapprove selected comments"

