import requests
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from decouple import config


@app.task
def send_email_with_shared_set(set_id: int, user_id: int, recipient_email: str):
    """
    Task to send an email with a shared set to the recipient.

    Args:
        set_id (int): The ID of the set.
        user_id (int): The ID of the user sharing the set.
        recipient_email (str): The email address of the recipient.

    """
    set_instance = Set.objects.get(id=set_id)
    email_content = render_to_string('email_set_detail.html', {'set': set_instance})

    response = requests.post(
        "https://api.eu.mailgun.net/v3/kindrat.planeks.org/messages",
        auth=("api", config('MAILGUN_API_KEY', None)),
        data={"from": config('EMAIL_HOST_USER', ''),
              "to": [f"{recipient_email}", ],
              "subject": "Shared Set",
              "html": email_content}
    )
    if response.status_code == 200:
        message_id = response.json().get("id").strip('<>')
        SharedSetEmail.objects.create(
            message_id=message_id,
            sender_id=user_id,
            set_object=set_instance,
            send_to=recipient_email
        )
    else:
        SharedSetEmail.objects.create(
            sender_id=user_id,
            set_object=set_instance,
            status='Not delivered',
            send_to=recipient_email
        )


@app.task
def check_emails_status():
    """
    Task to check the status of sent emails and update SharedSetEmail objects accordingly.

    """
    send_emails = SharedSetEmail.objects.filter(status__in=['Sent', 'Delivered'])
    for email_obj in send_emails:
        if (
                email_obj.status == 'Delivered'
                and email_obj.created_at.replace(tzinfo=None) < datetime.now() - timedelta(days=7)
        ):
            email_obj.status = 'Ignored'
            email_obj.save()
            continue

        message_id = email_obj.message_id
        response = requests.get(
            "https://api.eu.mailgun.net/v3/kindrat.planeks.org/events",
            auth=("api", config('MAILGUN_API_KEY', None)),
            params={"message-id": message_id,
                    "limit": 1}
        )
        email_obj_status = next(iter(response.json().get('items'))).get('event').capitalize()
        email_obj.status = email_obj_status
        email_obj.save()

        if email_obj_status == 'Opened':
            requests.post(
                "https://api.eu.mailgun.net/v3/kindrat.planeks.org/messages",
                auth=("api", config('MAILGUN_API_KEY', None)),
                data={"from": config('EMAIL_HOST_USER', ''),
                      "to": [f"{email_obj.sender.email}", ],
                      "subject": "Shared Set was opened",
                      "text": f"Your Shared Set: '{email_obj.set_object.name}' was opened by {email_obj.send_to}"}
            )
