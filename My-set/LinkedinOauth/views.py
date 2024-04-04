from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.exceptions import BadRequest
import logging


logger = logging.getLogger(__name__)


def linkedin_login_view(request):
    """
    Redirects user to LinkedIn login page.

    Returns:
        HttpResponseRedirect: A redirect to the LinkedIn login page.

    """
    return LinkedInConnector.login_to_provider()


def linkedin_login_callback(request):
    """
    Callback view for LinkedIn login.

    Args:
        request: The HTTP request.

    Returns:
        HttpResponseRedirect: A redirect to the index page upon successful login, or an error page otherwise.

    """
    if request.method == 'GET':
        try:
            LinkedInConnector.login(request)
            return redirect(reverse('index'))
        except BadRequest as e:
            logger.error(f'Linkedin login error: {e}')
            return render(request, "error_register_login_failed.html")

    return redirect(reverse("login_register"))