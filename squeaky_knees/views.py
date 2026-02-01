"""Views for sitemap, robots.txt, RSS feed, and health check."""

from django.db import connection
from django.db.utils import DatabaseError
from django.db.utils import OperationalError
from django.http import HttpResponse
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page


def sitemap_view(request):
    """Generate sitemap.xml for search engines."""

    from squeaky_knees.blog.models import BlogIndexPage
    from squeaky_knees.blog.models import BlogPage

    # Get all published blog pages
    blog_pages = BlogPage.objects.live().public().order_by("-date")

    # Get blog index page
    blog_index = BlogIndexPage.objects.live().public().first()

    context = {
        "blog_index": blog_index,
        "blog_pages": blog_pages,
        "site_url": request.build_absolute_uri("/").rstrip("/"),
    }

    xml_content = render_to_string("sitemap.xml", context)
    return HttpResponse(xml_content, content_type="application/xml")


@cache_page(60 * 60 * 24)  # Cache for 24 hours
def robots_txt_view(request):
    """Generate robots.txt for search engine crawlers."""
    context = {
        "site_url": request.build_absolute_uri("/").rstrip("/"),
    }

    txt_content = render_to_string("robots.txt", context)
    return HttpResponse(txt_content, content_type="text/plain")


def rss_feed_view(request):
    """Generate RSS feed for blog posts."""
    from squeaky_knees.blog.models import BlogPage

    # Get latest published blog posts (limit to 20)
    blog_posts = BlogPage.objects.live().public().order_by("-date")[:20]

    context = {
        "blog_posts": blog_posts,
        "site_url": request.build_absolute_uri("/").rstrip("/"),
        "site_name": "Squeaky Knees",
    }

    xml_content = render_to_string("feed.xml", context)
    return HttpResponse(xml_content, content_type="application/rss+xml")


def health_check(request):
    """Health check endpoint that verifies app and database connectivity.

    Returns:
        JSON response with status and database connection status.
    """
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return JsonResponse(
            {
                "status": "ok",
                "database": "connected",
            },
            status=200,
        )
    except (DatabaseError, OperationalError) as e:
        return JsonResponse(
            {
                "status": "error",
                "database": "disconnected",
                "error": str(e),
            },
            status=503,
        )
