import os
import tempfile
import fdb

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.apps import apps
from django.db import connection

from .data_loader import DataLoader, engine
from .forms import FileUploadForm
from .models.oms_data import DataType, DataImport, DataLoaderConfig
from ..home.models import MainSettings
from ..organization.models import MedicalOrganization
from ..peopledash.models import Organization


def upload_file(request, data_type_id):
    data_type = get_object_or_404(DataType, id=data_type_id)
    loader_config = get_object_or_404(DataLoaderConfig, data_type=data_type)
    organization = MedicalOrganization.objects.first()

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['csv_file']

            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                loader = DataLoader(
                    engine=engine,
                    table_name=loader_config.table_name,
                    data_type_name=data_type.name,
                    column_check=loader_config.column_check,
                    columns_for_update=loader_config.get_columns_for_update(),
                    encoding=loader_config.encoding,
                    sep=loader_config.delimiter,
                    clear_all_rows=loader_config.clear_all_rows
                )
                loader.load_data(temp_file_path)  # Загружаем данные

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': loader.message
                    })
                else:
                    context = {
                        'organization': organization,
                        'success': True,
                        'message': loader.message,
                        'data_type': data_type,
                        'form': form
                    }
                    return render(request, 'data_loader/upload_file.html', context)
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': str(e)
                    })
                else:
                    context = {
                        'organization': organization,
                        'success': False,
                        'message': str(e),
                        'data_type': data_type,
                        'form': form
                    }
                    return render(request, 'data_loader/upload_file.html', context)
            finally:
                # Удаляем временный файл после обработки
                os.remove(temp_file_path)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Некорректная форма.'
                })
            else:
                context = {
                    'organization': organization,
                    'success': False,
                    'message': 'Некорректная форма.',
                    'data_type': data_type,
                    'form': form
                }
                return render(request, 'data_loader/upload_file.html', context)
    else:
        form = FileUploadForm()

    return render(request, 'data_loader/upload_file.html',
                  {'organization': organization, 'form': form, 'data_type': data_type})


def data_upload_dashboard(request):
    data_types = DataType.objects.all()
    organization = MedicalOrganization.objects.first()
    categories = set(data_type.category for data_type in data_types)  # Собираем все категории
    firebird_status = check_kauz_connection()

    for data_type in data_types:
        # Получаем дату последней загрузки и сообщение
        last_import = DataImport.objects.filter(data_type=data_type).order_by('-date_added').first()
        data_type.last_import_date = last_import.date_added if last_import else None
        data_type.last_import_message = last_import.message if last_import else ""
        # Подсчитываем количество строк в таблице, проверяя наличие связанного DataLoaderConfig
        try:
            config = data_type.dataloaderconfig  # Проверка на наличие DataLoaderConfig
            if config and config.table_name:
                # Используем SQL-запрос для подсчета строк напрямую
                with connection.cursor() as cursor:
                    cursor.execute(f'SELECT COUNT(*) FROM {config.table_name}')
                    data_type.row_count = cursor.fetchone()[0]
            else:
                data_type.row_count = 1
        except DataLoaderConfig.DoesNotExist:
            # Если DataLoaderConfig для данного типа данных не существует
            data_type.row_count = 2

    return render(request, 'data_loader/data_upload_dashboard.html', {
        'organization': organization,
        'data_types': data_types,
        'categories': categories,
        'firebird_status': firebird_status
    })


def refresh_message(request, data_type_id):
    data_type = get_object_or_404(DataType, id=data_type_id)
    last_import = DataImport.objects.filter(data_type=data_type).order_by('-date_added').first()
    message = last_import.message if last_import else "Сообщение отсутствует."
    return JsonResponse({'message': message})


def refresh_data(request):
    data_types = DataType.objects.all()
    data = []

    for data_type in data_types:
        last_import = DataImport.objects.filter(data_type=data_type).order_by('-date_added').first()

        row_count = 0
        if data_type.dataloaderconfig and data_type.dataloaderconfig.table_name:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'SELECT COUNT(*) FROM {data_type.dataloaderconfig.table_name}')
                    row_count = cursor.fetchone()[0]
            except Exception as e:
                print(f"Ошибка подсчета строк для таблицы {data_type.dataloaderconfig.table_name}: {e}")

        data.append({
            'id': data_type.id,
            'name': data_type.name,
            'category_id': data_type.category.id,
            'category_name': data_type.category.name,
            'row_count': row_count,
            'last_import_date': last_import.date_added if last_import else None,
            'last_import_message': last_import.message if last_import else ""
        })

    return JsonResponse({'data_types': data})


def check_kauz_connection():
    settings = MainSettings.objects.first()
    if not settings:
        return "Настройки не найдены."

    dsn = f"{settings.kauz_server_ip}:{settings.kauz_database_path}"

    try:
        con = fdb.connect(
            dsn=dsn,
            user=settings.kauz_user,
            password=settings.kauz_password,
            charset='WIN1251',  # Указание кодировки
            port=settings.kauz_port
        )
        con.close()
        return "Подключение доступно"
    except Exception as e:
        return f"Ошибка подключения: {e}"


def get_table_row_counts(request):
    """ Возвращает количество строк для каждой таблицы """
    data_types = DataType.objects.all()
    organization = MedicalOrganization.objects.first()
    organization_name = organization.name if organization else "Не указано"
    data = []

    for data_type in data_types:
        row_count = 0
        if hasattr(data_type, 'dataloaderconfig') and data_type.dataloaderconfig.table_name:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'SELECT COUNT(*) FROM {data_type.dataloaderconfig.table_name}')
                    row_count = cursor.fetchone()[0]
            except Exception as e:
                row_count = f"Ошибка: {str(e)}"

        # Получение информации о последнем импорте
        last_import = DataImport.objects.filter(data_type=data_type).order_by('-date_added').first()
        last_import_date = last_import.date_added if last_import else None
        last_import_message = last_import.message if last_import else "Сообщение отсутствует."

        data.append({
            'data_type': data_type.name,
            'category': data_type.category.name if data_type.category else "Не указано",
            'row_count': row_count,
            'last_import_date': last_import_date,
            'last_import_message': last_import_message
        })

    return JsonResponse({
        'organization_name': organization_name,
        'tables': data
    })
