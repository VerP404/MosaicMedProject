# views.py
import csv
import os

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect

from .forms import FileUploadForm
from .utils import process_csv_file, CSV_TO_MODEL_MAPPING


class OMSDataUploadView(APIView):
    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file or not file.name.endswith('.csv'):
            return Response({"error": "Please upload a valid CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        # Сохраняем файл во временное хранилище
        file_name = default_storage.save(file.name, file)
        file_path = default_storage.path(file_name)

        try:
            # Обрабатываем файл
            process_csv_file(file_path)
            return Response({"status": "Data uploaded successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Удаляем файл после обработки
            default_storage.delete(file_name)


def validate_csv(file_content):
    # Получаем список обязательных столбцов из CSV_TO_MODEL_MAPPING
    required_columns = CSV_TO_MODEL_MAPPING.keys()

    try:
        # Читаем CSV и удаляем кавычки из заголовков
        reader = csv.DictReader(file_content.splitlines(), delimiter=';')
        columns = [col.lstrip('\ufeff').strip('"').strip("'") for col in reader.fieldnames]  # Удаляем кавычки и BOM


        # Логируем столбцы для диагностики
        print(f"Проверка столбцов в файле: {columns}")

        # Проверка обязательных столбцов
        missing_columns = [col for col in required_columns if col not in columns]
        return columns, missing_columns, None
    except Exception as e:
        return None, None, str(e)


def upload_file_view(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)

        # Если файл уже был проверен, но теперь подтверждается его загрузка
        if 'confirmed' in request.POST and request.POST.get('temp_file_path'):
            file_path = request.POST.get('temp_file_path')
            try:
                # Обрабатываем файл и загружаем данные в базу
                process_csv_file(file_path)
                return redirect('upload_success')  # Перенаправляем на страницу успеха
            except Exception as e:
                return render(request, 'upload_file.html', {
                    'form': form,
                    'error': f"Ошибка при загрузке файла: {str(e)}"
                })
            finally:
                # Удаляем временный файл после загрузки
                if os.path.exists(file_path):
                    default_storage.delete(file_path)

        # Изначально файл проверяется
        elif form.is_valid():
            file = form.cleaned_data['file']

            # Сохраняем файл во временное хранилище для последующей загрузки
            file_name = default_storage.save(file.name, file)
            file_path = default_storage.path(file_name)

            # Читаем содержимое файла для проверки
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Проверка структуры файла
            columns, missing_columns, error = validate_csv(file_content)

            if error:
                return render(request, 'data_loader/upload_file.html', {
                    'form': form,
                    'error': f"Ошибка при чтении файла: {error}"
                })

            if missing_columns:
                return render(request, 'data_loader/upload_file.html', {
                    'form': form,
                    'columns': columns,
                    'missing_columns': missing_columns,
                    'error': "Файл не соответствует шаблону. Не хватает обязательных столбцов."
                })

            # Если всё в порядке, отображаем кнопку загрузки
            return render(request, 'data_loader/upload_file.html', {
                'form': form,
                'columns': columns,
                'ready_for_upload': True,
                'temp_file_path': file_path  # Передаем путь к временному файлу для последующей загрузки
            })

    else:
        form = FileUploadForm()

    return render(request, 'data_loader/upload_file.html', {'form': form})