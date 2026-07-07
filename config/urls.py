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

from squeaky_knees.views import blog_view
from squeaky_knees.views import contact_success_view
from squeaky_knees.views import contact_view
from squeaky_knees.views import health_check
from squeaky_knees.views import home_view
from squeaky_knees.views import robots_txt_view
from squeaky_knees.views import rss_feed_view
from squeaky_knees.views import sitemap_view

# URL resolution order matters — Django stops at the FIRST match:
#
#   1. Explicit Django views ("/", /about/, /contact/, /blog/, admin, etc.)
#      win over Wagtail pages with the same slug. A Wagtail page with slug
#      "about" would be unreachable — pick slugs that don't collide.
#   2. path("blog/", blog_view) matches ONLY exactly /blog/. Children like
#      /blog/my-post/ fall through to the Wagtail catch-all below.
#   3. path("", include(wagtail_urls)) must stay LAST: it claims every
#      remaining URL and 404s anything that isn't a live Wagtail page.
#
# The Wagtail Site root is the tree root (see blog migration 0007), so a
# page's URL is exactly "/" + its slug path, e.g. /blog/my-post/.
urlpatterns = [
    path("", home_view, name="home"),
    path("health/", health_check, name="health"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    path("contact/", contact_view, name="contact"),
    path("contact/success/", contact_success_view, name="contact_success"),
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
    # Blog index (named URL + fallback when no BlogIndexPage exists)
    path("blog/", blog_view, name="blog_index"),
    # Your stuff: custom urls includes go here
    # ...
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    # Wagtail pages - place at end to catch remaining URLs
    # Mounted at root so Wagtail's generated URLs (e.g. /blog/) match Django's routing.
    path("", include(wagtail_urls)),
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
