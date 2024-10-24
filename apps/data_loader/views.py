from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from .data_loader import DataLoader, engine
from .forms import FileUploadForm
from .models.oms_data import DataType, DataImport, DataLoaderConfig
from ..organization.models import MedicalOrganization
from ..peopledash.models import Organization


def upload_file(request, data_type_id):
    data_type = get_object_or_404(DataType, id=data_type_id)
    loader_config = get_object_or_404(DataLoaderConfig, data_type=data_type)
    organization = MedicalOrganization.objects.first()

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save(commit=False)
            file_instance.data_type = data_type
            file_instance.save()

            try:
                loader = DataLoader(
                    engine=engine,
                    table_name=loader_config.table_name,
                    data_type_name=data_type.name,
                    column_check=loader_config.column_check,
                    columns_for_update=loader_config.get_columns_for_update(),
                    encoding=loader_config.encoding,
                    sep=loader_config.delimiter
                )
                loader.load_data(file_instance.csv_file.path)  # Загружаем данные

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    # Возвращаем JSON для AJAX-запросов
                    return JsonResponse({
                        'success': True,
                        'message': loader.message
                    })
                else:
                    # Стандартный рендеринг страницы
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
    for data_type in data_types:
        last_import = DataImport.objects.filter(data_type=data_type).order_by('-date_added').first()
        data_type.last_import_date = last_import.date_added if last_import else None

    return render(request, 'data_loader/data_upload_dashboard.html', {
        'organization': organization,
        'data_types': data_types,
        'categories': categories  # Передаем категории
    })
