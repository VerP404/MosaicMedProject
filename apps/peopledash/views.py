import pandas as pd
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import io
from .models import RegisteredPatients, TodayData, FourteenDaysData, Page, Building, Specialty, Organization
from .forms import UploadDataForm
from django.contrib import messages


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
    # Получаем объект Page для заданного path
    page = get_object_or_404(Page, path=path)

    # Извлекаем первую организацию
    organization = Organization.objects.first()

    # Получаем все Subdivision, связанные с Building, который указан на странице Page
    subdivisions = page.building.subdivisions.values_list('name', flat=True)

    # Фильтруем и группируем данные из RegisteredPatients по специальностям
    data_from_db = (
        RegisteredPatients.objects.filter(
            organization=organization.name,
            subdivision__in=subdivisions
        )
        .values('speciality')
        .annotate(
            total_slots_today=Sum('slots_today'),
            total_free_slots_today=Sum('free_slots_today'),
            total_slots_14_days=Sum('slots_14_days'),
            total_free_slots_14_days=Sum('free_slots_14_days')
        )
    )

    # Подготовка данных для JSON-ответа
    data = [
        {
            'Наименование должности': item['speciality'],
            'Всего_1': item['total_slots_today'],
            'Слоты свободные для записи_1': item['total_free_slots_today'],
            'Всего_14': item['total_slots_14_days'],
            'Слоты свободные для записи_14': item['total_free_slots_14_days'],
        }
        for item in data_from_db
    ]


    # Возвращаем данные в формате JSON
    return JsonResponse(data, safe=False)


def clean_and_validate_data(df):
    organizations = ['БУЗ ВО \"ВГКП № 3\"', 'БУЗ ВО \"ВГКП № 7\"', 'БУЗ ВО \"ВГКП № 18\"', 'БУЗ ВО \"ВГП № 16\"',
                     'БУЗ ВО \"Павловская РБ\"', 'БУЗ ВО \"Новоусманская РБ\"', 'БУЗ ВО \"Рамонская РБ\"',
                     'БУЗ ВО \"Бутурлиновская РБ\"']
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
    # Очищаем таблицу RegisteredPatients перед обновлением
    RegisteredPatients.objects.all().delete()

    # Добавляем данные из TodayData
    for record in TodayData.objects.all():
        RegisteredPatients.objects.create(
            organization=record.organization,
            subdivision=record.subdivision,
            speciality=record.speciality,
            slots_today=record.total_slots,
            free_slots_today=record.free_slots,
            slots_14_days=0,  # Изначально для данных "сегодня" поле на 14 дней будет пустым
            free_slots_14_days=0,
            report_datetime=report_dt.strftime('%H:%M %d.%m.%Y')
        )

    # Обновляем данные из FourteenDaysData
    for record in FourteenDaysData.objects.all():
        # Пытаемся найти совпадение по organization, subdivision и speciality
        existing_record = RegisteredPatients.objects.filter(
            organization=record.organization,
            subdivision=record.subdivision,
            speciality=record.speciality
        ).first()

        if existing_record:
            # Обновляем поля для данных на 14 дней в существующей записи
            existing_record.slots_14_days = record.total_slots
            existing_record.free_slots_14_days = record.free_slots
            existing_record.save()
        else:
            # Если записи нет, добавляем новую
            RegisteredPatients.objects.create(
                organization=record.organization,
                subdivision=record.subdivision,
                speciality=record.speciality,
                slots_today=0,  # Для данных на 14 дней слоты на сегодня будут пустыми
                free_slots_today=0,
                slots_14_days=record.total_slots,
                free_slots_14_days=record.free_slots,
                report_datetime=report_dt.strftime('%H:%M %d.%m.%Y')
            )


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


def registered_patients_api(request):
    # Получаем все данные из RegisteredPatients
    data = RegisteredPatients.objects.values(
        'organization',
        'subdivision',
        'speciality',
        'slots_today',
        'free_slots_today',
        'slots_14_days',
        'free_slots_14_days',
        'report_datetime'
    )

    # Преобразуем данные в список
    data_list = list(data)

    # Возвращаем данные в формате JSON
    return JsonResponse(data_list, safe=False)
