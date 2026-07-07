from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from wagtail.users.apps import WagtailUsersAppConfig as BaseWagtailUsersAppConfig


class UsersConfig(AppConfig):
    # default = True marks this as the AppConfig for the local users app,
    # since this module now also defines WagtailUsersAppConfig below.
    default = True
    name = "squeaky_knees.users"
    verbose_name = _("Users")

    def ready(self):
        """
        Override this method in subclasses to run code when Django starts.
        """


class WagtailUsersAppConfig(BaseWagtailUsersAppConfig):
    """Referenced from INSTALLED_APPS in place of "wagtail.users".

    Points Wagtail's user management at our custom viewset, whose forms
    use the User model's single ``name`` field instead of the
    first_name/last_name fields this project's User model removed.
    """

    user_viewset = "squeaky_knees.users.viewsets.UserViewSet"
