from django.urls import path

from . import views

app_name = "blog"
urlpatterns = [
    path("comment/<int:page_id>/", views.add_comment, name="add_comment"),
    path("", views.moderate_comments, name="moderate_comments"),
]
