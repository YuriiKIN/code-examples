from typing import Any
import requests

from django.contrib.auth import get_user_model
from rest_framework.request import Request
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_field, user_username, user_email
from allauth.utils import valid_email_or_none
from allauth.socialaccount import app_settings
from allauth.socialaccount.providers.keycloak.provider import KeycloakProvider
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)


class CustomSocialAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for populating user data during social account login/signup.
    """

    def populate_user(self, request: Request, sociallogin: Any, data: dict[str, Any]) -> get_user_model():
        """
        Populate user data during social account login/signup.

        Args:
            request: The HTTP request.
            sociallogin: The social login instance.
            data: Dictionary containing user data.

        Returns:
            User: The populated user object.
        """
        username = data.get("username")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        name = data.get("name")
        user_groups = data.get("groups")
        user = sociallogin.user
        user_username(user, username or "")
        user_email(user, valid_email_or_none(email) or "")
        name_parts = (name or "").partition(" ")
        user_field(user, "first_name", first_name or name_parts[0])
        user_field(user, "last_name", last_name or name_parts[2])
        try:
            for group in user_groups:
                if group == "/admins":
                    user_field(user, "is_superuser", "True")
                    user_field(user, "is_staff", "True")
                if group == "/editors":
                    user_field(user, "is_staff", "True")
        except TypeError:
            user_field(user, "is_active", "True")
        return user


class KeycloakOAuth2Adapter(OAuth2Adapter):
    """
    Adapter for Keycloak OAuth2 provider.
    """
    provider_id = KeycloakProvider.id
    supports_state = True

    settings = app_settings.PROVIDERS.get(provider_id, {})
    provider_base_url = "{0}/realms/{1}".format(
        settings.get("KEYCLOAK_URL"), settings.get("KEYCLOAK_REALM")
    )

    authorize_url = "{0}/protocol/openid-connect/auth".format(provider_base_url)

    other_url = settings.get("KEYCLOAK_URL_ALT")
    if other_url is None:
        other_url = settings.get("KEYCLOAK_URL")

    server_base_url = "{0}/realms/{1}".format(other_url, settings.get("KEYCLOAK_REALM"))
    access_token_url = "{0}/protocol/openid-connect/token".format(server_base_url)
    profile_url = "{0}/protocol/openid-connect/userinfo".format(server_base_url)

    def complete_login(self, request: Request, app: Any, token: Any, response: Any) -> SocialLogin:
        """
        Complete the login process.

        Args:
            request: The HTTP request.
            app: The application instance.
            token: The access token.
            response: The response received from the OAuth provider.

        Returns:
            SocialLogin: The social login instance.
        """
        response = requests.post(
            self.profile_url, headers={"Authorization": "Bearer " + str(token)}
        )
        response.raise_for_status()
        extra_data = response.json()
        extra_data["id"] = extra_data["sub"]
        del extra_data["sub"]

        return self.get_provider().sociallogin_from_response(request, extra_data)


oauth2_login = OAuth2LoginView.adapter_view(KeycloakOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(KeycloakOAuth2Adapter)
