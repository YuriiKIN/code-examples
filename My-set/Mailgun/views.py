import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def share_set_via_email(request):
    """
    View to share a set via email.

    POST request should include the set ID and recipient's email address.

    Returns:
        JsonResponse: JSON response indicating success or failure.

    """
    if request.method == 'POST':
        data = json.loads(request.body)
        set_id = data.get('set_id')
        if not set_id:
            return JsonResponse({'success': False}, status=404)

        recipient_email = data.get('email')
        send_email_with_shared_set.delay(set_id, request.user.id, recipient_email)
        return JsonResponse({'success': True}, status=200)

    return JsonResponse({'success': False}, status=404)
