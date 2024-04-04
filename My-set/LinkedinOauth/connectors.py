from abc import ABC, abstractmethod
from urllib.parse import urlencode

import requests
from django.core.exceptions import BadRequest
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.conf import settings


class OpenIDConnector(ABC):

    @abstractmethod
    def login_to_provider(self):
        """
        This method should handle the logic for obtaining the authorization code.
        """
        pass

    @abstractmethod
    def get_authorization_code(self, request):
        """
        This method should get authorization code from request
        """
        pass

    @abstractmethod
    def get_access_token(self, authorization_code):
        """
        This method should handle the logic for exchanging the authorization code
        for an access token.
        """
        pass

    @abstractmethod
    def get_userinfo(self, access_token):
        """
        This method should handle the logic for obtaining user information
        using the provided access token.
        """
        pass

    @abstractmethod
    def populate_user(self, userinfo):
        """
        This method should handle the logic to populate user data based on
        the user information obtained from the OpenID Connect provider.

        Args:
            userinfo: The user information obtained from the OpenID Connect provider.
        """
        pass

    @abstractmethod
    def login(self, request):
        """
        This method should handle the overall login logic, including
        obtaining the authorization code, exchanging it for an access token,
        and obtaining user information.
        """
        pass


class LinkedInConnector(OpenIDConnector):

    @classmethod
    def _bad_request_check(cls, response):
        """
        Checks for bad request response.

        Args:
            response: The response object.

        Raises:
            BadRequest: If the response status code is not 200.

        """
        if response.status_code != 200:
            raise BadRequest

    @classmethod
    def login_to_provider(cls):
        """
        Redirects user to LinkedIn authorization page.

        Returns:
            HttpResponseRedirect: A redirect to the LinkedIn authorization URL.

        """
        authorize_url = "https://www.linkedin.com/oauth/v2/authorization/?"

        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URL,
            "state": "ASDFASDFASDF",
            "scope": "profile,email,openid"
        }

        return redirect(authorize_url + urlencode(params))

    @classmethod
    def get_authorization_code(self, request) -> str:
        """
        Retrieves the authorization code from the request.

        Args:
            request: The HTTP request.

        Returns:
            str: The authorization code.

        """
        return request.GET.get("code")

    @classmethod
    def get_access_token(cls, authorization_code: str) -> str:
        """
        Retrieves the access token.

        Args:
            authorization_code (str): The authorization code.

        Returns:
            str: The access token.

        """
        access_token_url = "https://www.linkedin.com/oauth/v2/accessToken"

        data = {
            "code": authorization_code,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URL,
            "grant_type": "authorization_code",
        }

        response = requests.post(access_token_url, data=data)
        cls._bad_request_check(response)
        return response.json().get("access_token")

    @classmethod
    def get_userinfo(cls, access_token: str) -> dict:
        """
        Retrieves user information.

        Args:
            access_token (str): The access token.

        Returns:
            dict: User information.

        """
        profile_url = "https://api.linkedin.com/v2/userinfo"

        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = requests.get(profile_url, headers=headers)
        cls._bad_request_check(userinfo_response)
        return userinfo_response.json()

    @classmethod
    def populate_user(cls, userinfo: dict) -> get_user_model():
        """
        Populates user information.

        Args:
            userinfo (dict): User information.

        Returns:
            User: The user object.

        """
        user_email = userinfo.get("email")
        user_name = userinfo.get("name")

        if get_user_model().objects.filter(email=user_email).exists():
            linkedin_user = get_user_model().objects.filter(
                email=user_email
            ).first()
        else:
            linkedin_user = get_user_model().objects.create_user(
                email=user_email,
                name=user_name,
                is_linkedin_user=True
            )

        return linkedin_user

    @classmethod
    def login(cls, request):
        """
        Performs login action.

        Args:
            request: The HTTP request.

        """
        authorization_code = cls.get_authorization_code(request)
        access_token = cls.get_access_token(authorization_code)
        userinfo = cls.get_userinfo(access_token)

        linkedin_user = cls.populate_user(userinfo=userinfo)
        linkedin_user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, linkedin_user)
