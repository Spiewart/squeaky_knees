from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.blocks import CharBlock
from wagtail.blocks import RichTextBlock
from wagtail.blocks import StructBlock
from wagtail.blocks import TextBlock
from wagtail.fields import RichTextField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index


class CodeBlock(StructBlock):
    """A dedicated code block for displaying code snippets."""

    language = CharBlock(
        max_length=50,
        help_text="Programming language (e.g., python, javascript, html)",
        required=False,
    )
    code = TextBlock(help_text="Your code here")

    class Meta:
        template = "blog/blocks/code_block.html"
        icon = "code"
        label = "Code"


class BlogIndexPage(Page):
    """Main blog page that lists all blog posts."""

    intro = RichTextField(blank=True)
    posts_per_page = 10  # Number of blog posts per page

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_context(self, request):
        """Add blog posts to template context with pagination."""
        context = super().get_context(request)
        # Get all live child pages (BlogPages) that are direct children of this page
        all_blogpages = (
            self.get_children()
            .live()
            .type(BlogPage)
            .specific()
            .order_by("-blogpage__date")
        )

        # Paginate the blog posts
        paginator = Paginator(all_blogpages, self.posts_per_page)
        page_number = request.GET.get("page", 1)

        from django.core.paginator import InvalidPage

        try:
            page_obj = paginator.page(page_number)
        except InvalidPage:
            # If page number is invalid, return first page
            page_obj = paginator.page(1)

        context["page_obj"] = page_obj
        context["blogpages"] = page_obj.object_list
        context["paginator"] = paginator
        context["is_paginated"] = paginator.num_pages > 1
        return context


class BlogPageTag(TaggedItemBase):
    """Tags for blog posts."""

    content_object = ParentalKey(
        "BlogPage",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )


class BlogPage(Page):
    """Individual blog post page."""

    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = StreamField(
        [
            ("rich_text", RichTextBlock()),
            ("code", CodeBlock()),
        ],
        blank=True,
    )
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    header_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Header image for the blog post",
    )

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("date"),
                FieldPanel("tags"),
                FieldPanel("header_image"),
            ],
            heading="Blog post details",
        ),
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    def get_context(self, request):
        """Add approved comments to context."""
        from django.conf import settings

        from .forms import CommentForm

        context = super().get_context(request)
        # Get approved top-level comments only (parent=None)
        root_comments = Comment.objects.filter(
            blog_page=self,
            approved=True,
            parent__isnull=True,
        ).order_by("created")
        context["comments"] = root_comments
        context["comment_form"] = CommentForm()
        context["recaptcha_site_key"] = settings.RECAPTCHA_PUBLIC_KEY
        return context


class Comment(ClusterableModel):
    """Comments on blog posts with support for nested replies."""

    blog_page = ParentalKey(
        BlogPage,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_comments",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        help_text="Parent comment this is a reply to",
    )
    text = StreamField(
        [
            ("rich_text", RichTextBlock()),
            ("code", CodeBlock()),
        ],
        blank=False,
    )
    created = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(
        default=False,
        help_text="Comments must be approved by admin before appearing on the site",
    )

    panels = [
        FieldPanel("author"),
        FieldPanel("parent"),
        FieldPanel("text"),
        FieldPanel("approved"),
    ]

    class Meta:
        ordering = ["created"]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.blog_page.title}"

    def is_reply(self):
        """Check if this comment is a reply to another comment."""
        return self.parent is not None

    def get_root_comment(self):
        """Get the root (top-level) comment of this thread."""
        current = self
        while current.parent:
            current = current.parent
        return current

    def get_depth(self):
        """Get depth of this comment in the reply chain (0 for top-level)."""
        depth = 0
        current = self
        while current.parent:
            depth += 1
            current = current.parent
        return depth

    def get_all_replies(self, *, approved_only: bool = True):
        """Get all replies to this comment recursively."""
        replies = []
        direct_replies = (
            self.replies.filter(approved=True) if approved_only else self.replies.all()
        )
        for reply in direct_replies:
            replies.append(reply)
            replies.extend(reply.get_all_replies(approved_only=approved_only))
        return replies
