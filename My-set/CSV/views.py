from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from celery.result import AsyncResult


@login_required
def upload_csv_view(request):
    """
    View function to handle uploading CSV files and processing them asynchronously.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response.

    """
    if request.method == 'POST' and request.FILES:
        csv_file = request.FILES['csv_file']

        if not csv_file.name.endswith('.csv'):
            message = '* The file should be in CSV format'
            return render(request, 'upload_csv.html', {'message': message})

        csv_content = csv_file.read().decode('utf-8')
        task = process_csv_file.delay(csv_content, request.user.id)
        data = {
            'filename': csv_file.name,
            'task_id': task.id
        }

        return render(request, 'upload_csv_success.html', data)

    return render(request, 'upload_csv.html')


@login_required
def check_upload_status(request):
    """
    View function to check the status of the CSV processing task.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response.

    """
    task_id = request.GET.get('task_id')
    filename = request.GET.get('filename')
    error_message = None
    objects_created = None
    objects_updated = None

    if task_id:
        task_result = AsyncResult(task_id)
        if task_result.ready():
            if task_result.successful():
                objects_created, objects_updated = task_result.get()

            else:
                error_message = task_result.result

        data = {
            'task_id': task_id,
            'filename': filename,
            'task_status': task_result.status,
            'error_message': error_message,
            'objects_created': objects_created,
            'objects_updated': objects_updated,
        }

        return render(request, 'check_upload_status.html', data)
    return redirect(request, 'upload_csv')
