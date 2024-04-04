from typing import Any

OVERRIDE_NAME = (
    getattr(settings, "SOCIALACCOUNT_PROVIDERS", {})
    .get("keycloak", {})
    .get("OVERRIDE_NAME", "Keycloak")
)


class KeycloakAccount(ProviderAccount):
    def get_avatar_url(self) -> str:
        """
        Get the avatar URL from extra data.

        Returns:
            str: The avatar URL.
        """
        return self.account.extra_data.get("picture")

    def to_str(self) -> str:
        """
        Convert account to a string.

        Returns:
            str: The string representation of the account.
        """
        dflt = super(KeycloakAccount, self).to_str()
        return self.account.extra_data.get("name", dflt)


class CustomKeycloakProvider(KeycloakProvider):

    def extract_common_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract common fields from data.

        Args:
            data: Dictionary containing user data.

        Returns:
            Dict[str, Any]: Extracted common fields.
        """
        return dict(
            email=data.get("email"),
            username=data.get("preferred_username"),
            name=data.get("name"),
            user_id=data.get("user_id"),
            groups=data.get("Groups"),
            picture=data.get("picture"),
        )


provider_classes = [CustomKeycloakProvider]
