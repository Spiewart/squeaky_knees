"""Custom Wagtail user management viewset.

Wired up via WagtailUsersAppConfig in apps.py (which replaces
"wagtail.users" in INSTALLED_APPS).
"""

from wagtail.users.views.users import UserViewSet as WagtailUserViewSet

from .forms import UserCreationForm
from .forms import UserEditForm


class UserViewSet(WagtailUserViewSet):
    """Use forms and templates with a single Name field."""

    create_template_name = "wagtailusers/users/create_with_name.html"
    edit_template_name = "wagtailusers/users/edit_with_name.html"

    def get_form_class(self, for_update=False):  # noqa: FBT002 (Wagtail signature)
        if for_update:
            return UserEditForm
        return UserCreationForm
