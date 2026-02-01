from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from squeaky_knees.views import health_check
from squeaky_knees.views import robots_txt_view
from squeaky_knees.views import rss_feed_view
from squeaky_knees.views import sitemap_view

urlpatterns = [
    path("health/", health_check, name="health"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    # Sitemap, robots.txt, and RSS feed
    path("sitemap.xml", sitemap_view, name="sitemap"),
    path("robots.txt", robots_txt_view, name="robots"),
    path("feed.xml", rss_feed_view, name="rss_feed"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("squeaky_knees.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Wagtail Admin
    path("cms/", include(wagtailadmin_urls)),
    # Wagtail Documents
    path("documents/", include(wagtaildocs_urls)),
    # Blog app actions (comment submission, etc.)
    path("blog/actions/", include("squeaky_knees.blog.urls", namespace="blog")),
    # Your stuff: custom urls includes go here
    # ...
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    # Wagtail pages - place at end to catch remaining URLs
    path("blog/", include(wagtail_urls)),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]
