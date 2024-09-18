# views.py
import os
from django.shortcuts import render
from .forms import FileUploadForm
from .tasks import process_oms_data
from django.conf import settings
from celery.result import AsyncResult
from django.http import JsonResponse

def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            file_path = os.path.join(settings.MEDIA_ROOT, file.name)

            # Сохраняем файл на диск
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            # Запускаем асинхронную задачу с Celery
            task = process_oms_data.delay(file_path)

            return JsonResponse({'task_id': task.id}, status=202)
    else:
        form = FileUploadForm()
    return render(request, 'admin/omsdata/upload.html', {'form': form})

def task_status(request, task_id):
    task = AsyncResult(task_id)
    response = {
        'task_id': task_id,
        'state': task.state,
        'info': task.info,
    }
    return JsonResponse(response)
