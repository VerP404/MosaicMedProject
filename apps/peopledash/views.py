import pandas as pd
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import io
from .models import RegisteredPatients, TodayData, FourteenDaysData, Page, Building, Specialty, Organization
from .forms import UploadDataForm
from django.contrib import messages
import datetime


def index(request):
    organization = Organization.objects.first()
    first_record = RegisteredPatients.objects.first()
    report_datetime = first_record.report_datetime if first_record else None
    pages = Page.objects.all()
    context = {
        'report_datetime': report_datetime,
        'pages': pages,
        'organization': organization,
    }
    return render(request, 'peopledash/index.html', context)


def get_report_datetime(request):
    first_record = RegisteredPatients.objects.first()
    report_datetime = first_record.report_datetime if first_record else None
    return JsonResponse({'report_datetime': report_datetime})


def dynamic_page(request, path):
    organization = Organization.objects.first()
    page = get_object_or_404(Page, path=path)
    data_from_db = RegisteredPatients.objects.filter(subdivision=page.subdivision)
    first_record = RegisteredPatients.objects.first()
    report_datetime = first_record.report_datetime if first_record else None
    context = {
        'page': page,
        'data_from_db': data_from_db,
        'report_datetime': report_datetime,
        'url_data': f'/peopledash/get_data_{path}/',  # Добавьте 'peopledash/' к пути
        'organization': organization,
    }
    return render(request, 'peopledash/base_peopledash.html', context)


def dynamic_page_get_data(request, path):
    # Проверка, что объект Page существует для данного path
    page = get_object_or_404(Page, path=path)
    # Извлечение данных из RegisteredPatients
    data_from_db = RegisteredPatients.objects.filter(subdivision=page.subdivision)
    data = [
        {
            'Наименование должности': row.speciality,
            'Всего_1': row.slots_today,
            'Слоты свободные для записи_1': row.free_slots_today,
            'Слоты свободные для записи_14': row.free_slots_14_days,
        }
        for row in data_from_db
    ]
    # Возвращаем данные в формате JSON
    return JsonResponse(data, safe=False)


def clean_and_validate_data(df):
    organizations = list(Organization.objects.values_list('name', flat=True))
    df = df[(df['Наименование МО'].isin(organizations)) & (df['Тип приёма'] == 'Первичный прием')]

    df = df.dropna(
        subset=['Всего', 'в т.ч. слоты для ЕПГУ (создано)', 'Слоты свободные для записи', 'в т.ч. свободные для ЕПГУ'])

    numeric_columns = ['Всего', 'в т.ч. слоты для ЕПГУ (создано)', 'Слоты свободные для записи',
                       'в т.ч. свободные для ЕПГУ']
    for column in numeric_columns:
        df[column] = df[column].apply(lambda x: int(x) if str(x).isdigit() else 0)

    return df


def save_today_data(df, report_dt):
    TodayData.objects.all().delete()

    df = clean_and_validate_data(df)

    for index, row in df.iterrows():
        TodayData.objects.create(
            organization=row['Наименование МО'],
            subdivision=row['Обособленное подразделение'],
            speciality=row['Наименование должности'],
            doctor_name=row['Врач'],
            reception_type=row['Тип приёма'],
            total_slots=row['Всего'],
            epgu_slots=row['в т.ч. слоты для ЕПГУ (создано)'],
            free_slots=row['Слоты свободные для записи'],
            free_epgu_slots=row['в т.ч. свободные для ЕПГУ'],
            report_datetime=report_dt
        )


def save_fourteen_days_data(df, report_dt):
    FourteenDaysData.objects.all().delete()

    df = clean_and_validate_data(df)

    for index, row in df.iterrows():
        FourteenDaysData.objects.create(
            organization=row['Наименование МО'],
            subdivision=row['Обособленное подразделение'],
            speciality=row['Наименование должности'],
            doctor_name=row['Врач'],
            reception_type=row['Тип приёма'],
            total_slots=row['Всего'],
            epgu_slots=row['в т.ч. слоты для ЕПГУ (создано)'],
            free_slots=row['Слоты свободные для записи'],
            free_epgu_slots=row['в т.ч. свободные для ЕПГУ'],
            report_datetime=report_dt
        )


def process_transformer_files(report_dt):
    specialties = list(Specialty.objects.values_list('name', flat=True))
    organizations = list(Organization.objects.values_list('name', flat=True))
    corpus_mapping = {}
    for page in Page.objects.all():
        filters = list(page.building.subdivisions.values_list('name', flat=True))
        corpus_mapping[page.subdivision] = filters

    def filter_and_group(model):
        result = []
        records = model.objects.filter(
            organization__in=organizations,
            reception_type='Первичный прием',
            speciality__in=specialties
        )
        for record in records:
            for corpus, filters in corpus_mapping.items():
                if record.subdivision in filters:
                    result.append({
                        'Обособленное подразделение': corpus,
                        'Наименование должности': record.speciality,
                        'Всего': record.total_slots,
                        'Слоты свободные для записи': record.free_slots
                    })
        return result

    def aggregate_data(data):
        aggregated = {}
        for item in data:
            key = (item['Обособленное подразделение'], item['Наименование должности'])
            if key not in aggregated:
                aggregated[key] = {
                    'Всего': 0,
                    'Слоты свободные для записи': 0
                }
            aggregated[key]['Всего'] += item['Всего']
            aggregated[key]['Слоты свободные для записи'] += item['Слоты свободные для записи']
        return aggregated

    def merge_data(gr_1, gr_14):
        merged = {}
        all_keys = set(gr_1.keys()).union(set(gr_14.keys()))
        for key in all_keys:
            merged[key] = {
                'Всего_1': gr_1.get(key, {}).get('Всего', 0),
                'Слоты свободные для записи_1': gr_1.get(key, {}).get('Слоты свободные для записи', 0),
                'Всего_14': gr_14.get(key, {}).get('Всего', 0),
                'Слоты свободные для записи_14': gr_14.get(key, {}).get('Слоты свободные для записи', 0),
            }
        return merged

    def save_registered_patients_from_data(data, report_dt):
        RegisteredPatients.objects.all().delete()
        formatted_date = report_dt.strftime('%H:%M %d.%m.%Y')  # Форматируем дату
        for key, values in data.items():
            subdivision, speciality = key
            RegisteredPatients.objects.create(
                subdivision=subdivision,
                speciality=speciality,
                slots_today=values['Всего_1'],
                free_slots_today=values['Слоты свободные для записи_1'],
                slots_14_days=values['Всего_14'],
                free_slots_14_days=values['Слоты свободные для записи_14'],
                report_datetime=formatted_date  # Используем отформатированную дату
            )

    gr_1 = filter_and_group(TodayData)
    gr_14 = filter_and_group(FourteenDaysData)

    aggregated_gr_1 = aggregate_data(gr_1)
    aggregated_gr_14 = aggregate_data(gr_14)

    merged_data = merge_data(aggregated_gr_1, aggregated_gr_14)

    if merged_data:
        save_registered_patients_from_data(merged_data, report_dt)
    else:
        print("Нет данных для сохранения.")


def upload_data(request):
    organization = Organization.objects.first()
    if request.method == 'POST':
        form = UploadDataForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Очищаем таблицы перед загрузкой новых данных
                TodayData.objects.all().delete()
                FourteenDaysData.objects.all().delete()

                messages.info(request, 'Данные в таблице "Сегодня" очищены.')
                messages.info(request, 'Данные в таблице "14 дней" очищены.')

                file_today = request.FILES['file_today']
                df_today = pd.read_csv(io.BytesIO(file_today.read()), encoding='cp1251', delimiter=';')

                file_14_days = request.FILES['file_14_days']
                df_14_days = pd.read_csv(io.BytesIO(file_14_days.read()), encoding='cp1251', delimiter=';')

                report_datetime = form.cleaned_data['report_datetime']

                # Сохранение новых данных в модели
                save_today_data(df_today, report_datetime)
                save_fourteen_days_data(df_14_days, report_datetime)

                messages.success(request, 'Данные за сегодня успешно сохранены.')
                messages.success(request, 'Данные за 14 дней успешно сохранены.')

                # Обработка данных и формирование отчета
                process_transformer_files(report_datetime)
                messages.success(request, 'Данные успешно обработаны и обновлены.')

            except Exception as e:
                # Ловим любые ошибки и выводим сообщение
                messages.error(request, f'Произошла ошибка при обработке данных: {str(e)}')

            return redirect('upload_data')
        else:
            messages.error(request, 'Ошибка в форме. Пожалуйста, проверьте данные и попробуйте снова.')
    else:
        form = UploadDataForm()

    return render(request, 'peopledash/upload_data.html', {'form': form, 'organization': organization})


def notify_television_updates():
    channel_layer = get_channel_layer()
    data = list(RegisteredPatients.objects.values(
        'speciality', 'slots_today', 'free_slots_today', 'free_slots_14_days'
    ))
    async_to_sync(channel_layer.group_send)(
        "television_group",
        {
            "type": "send_update",
            "data": data  # Отправляем данные для обновления таблицы
        }
    )

