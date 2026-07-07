"""Tests for the Wagtail admin user forms (single name field)."""

import pytest
from django.urls import reverse

from squeaky_knees.users.forms import UserCreationForm
from squeaky_knees.users.forms import UserEditForm
from squeaky_knees.users.models import User


class TestWagtailUserForms:
    def test_edit_form_has_name_not_first_last(self):
        form = UserEditForm()
        assert "name" in form.fields
        assert "first_name" not in form.fields
        assert "last_name" not in form.fields

    def test_creation_form_has_name_not_first_last(self):
        form = UserCreationForm()
        assert "name" in form.fields
        assert "first_name" not in form.fields
        assert "last_name" not in form.fields

    @pytest.mark.django_db
    def test_edit_form_saves_name(self):
        user = User.objects.create_user(username="tabby", password="pw12345678")
        form = UserEditForm(
            instance=user,
            data={
                "username": "tabby",
                "name": "Tabitha Ewart",
                "email": "t@example.com",
            },
        )
        assert form.is_valid(), form.errors
        form.save()
        user.refresh_from_db()
        assert user.name == "Tabitha Ewart"

    @pytest.mark.django_db
    def test_user_display_name_uses_name(self):
        user = User.objects.create_user(
            username="tabby",
            password="pw12345678",
            name="Tabitha Ewart",
        )
        assert user.get_full_name() == "Tabitha Ewart"
        # Never "None None" (AbstractUser behavior with removed fields)
        user.name = ""
        assert user.get_full_name() == "tabby"


@pytest.mark.django_db
class TestWagtailUserAdminViews:
    def test_edit_page_renders_name_field(self, client):
        admin = User.objects.create_superuser(
            username="dave",
            email="d@example.com",
            password="pw12345678",
        )
        client.force_login(admin)
        response = client.get(
            reverse("wagtailusers_users:edit", args=[admin.pk]),
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert 'name="name"' in content
        assert 'name="first_name"' not in content

    def test_edit_saves_name_via_view(self, client):
        admin = User.objects.create_superuser(
            username="dave",
            email="d@example.com",
            password="pw12345678",
        )
        client.force_login(admin)
        response = client.post(
            reverse("wagtailusers_users:edit", args=[admin.pk]),
            {
                "username": "dave",
                "name": "Dave Ewart",
                "email": "d@example.com",
                "is_active": "on",
                "is_superuser": "on",
            },
        )
        assert response.status_code == 302
        admin.refresh_from_db()
        assert admin.name == "Dave Ewart"
