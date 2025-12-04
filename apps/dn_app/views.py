import os
import tempfile
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .forms import DNCSVUploadForm
from .services.csv_processor import DNCSVProcessor
from .models import DataImport


@require_http_methods(["GET", "POST"])
def upload_csv(request):
    """View для загрузки CSV файлов диспансерного наблюдения"""
    if request.method == 'POST':
        form = DNCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['csv_file']
            year = form.cleaned_data['year']
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Обрабатываем файл
                processor = DNCSVProcessor(temp_file_path, year)
                success, message = processor.process()
                
                if success:
                    stats = processor.stats
                    detailed_message = (
                        f"{message}\n\n"
                        f"Статистика обработки:\n"
                        f"- Всего строк: {stats['total_rows']}\n"
                        f"- Обработано: {stats['processed_rows']}\n"
                        f"- Создано пациентов: {stats['created_persons']}\n"
                        f"- Обновлено пациентов: {stats['updated_persons']}\n"
                        f"- Создано встреч: {stats['created_encounters']}\n"
                        f"- Создано наблюдений: {stats['created_observations']}\n"
                        f"- Откреплено пациентов: {stats.get('detached_count', 0)}"
                    )
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': detailed_message,
                            'stats': stats
                        })
                    else:
                        messages.success(request, detailed_message)
                        return redirect('dn_app:upload_csv')
                else:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': message
                        })
                    else:
                        messages.error(request, message)
            
            except Exception as e:
                error_message = f"Ошибка при обработке файла: {str(e)}"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_message
                    })
                else:
                    messages.error(request, error_message)
            
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Ошибка валидации формы',
                    'errors': form.errors
                })
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = DNCSVUploadForm()
    
    # Получаем последние загрузки
    recent_imports = DataImport.objects.all()[:10]
    
    context = {
        'form': form,
        'recent_imports': recent_imports
    }
    
    return render(request, 'dn_app/upload_csv.html', context)
