from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "squeaky_knees.blog"
    verbose_name = "Blog"
