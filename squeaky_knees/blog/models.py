from django.conf import settings
from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import InlinePanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.search import index


class BlogIndexPage(Page):
    """Main blog page that lists all blog posts."""

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_context(self, request):
        """Add blog posts to template context."""
        context = super().get_context(request)
        blogpages = self.get_children().live().order_by("-first_published_at")
        context["blogpages"] = blogpages
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
    body = RichTextField(blank=True)
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
        InlinePanel("comments", label="Comments"),
    ]

    def get_context(self, request):
        """Add approved comments to context."""
        from .forms import CommentForm

        context = super().get_context(request)
        context["comments"] = self.comments.filter(approved=True).order_by("created")
        context["comment_form"] = CommentForm()
        return context


class Comment(models.Model):
    """Comments on blog posts."""

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
    text = models.TextField(max_length=1000)
    created = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(
        default=False,
        help_text="Comments must be approved by admin before appearing on the site",
    )

    panels = [
        FieldPanel("author"),
        FieldPanel("text"),
        FieldPanel("approved"),
    ]

    class Meta:
        ordering = ["created"]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.blog_page.title}"
