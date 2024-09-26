import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
import pandas as pd
from datetime import datetime

file_loader_bp = Blueprint('file_loader', __name__)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../files'))

# Словарь с типами данных, внутренними папками, расширениями и ожидаемыми заголовками
file_info = {
    'info': {
        'area_data': ('csv', 'участки', ['Корпус', 'Участок', 'Врач'],
                      {'sep': ';', 'low_memory': False, 'dtype': 'str'}),
        'dn168n_data': ('csv', '168н', ['Код МКБ', 'Профиль', 'Специальность'],
                        {'sep': ';', 'low_memory': False, 'dtype': 'str'}),
        'naselenie_data': ('xlsx', 'население', ['ФИО Врача', 'Корпус', 'Профиль'], {'dtype': 'str'})
    },
    'iszl': {
        'iszl_data': ('csv', 'ИСЗЛ', ['pID', 'ldwID', 'pdwID'],
                      {'sep': ';', 'low_memory': False, 'dtype': 'str', 'encoding': 'cp1251'}),
        'people_data': ('csv', 'население', ['PID', 'FIO', 'DR'],
                        {'sep': ';', 'low_memory': False, 'dtype': 'str'})
    },
    'kvazar': {
        'emd_data': ('csv', 'ЭМД', ['ИД', 'ИД исходного ЭПМЗ', 'Дата документа'],
                     {'sep': ';', 'low_memory': False, 'dtype': 'str', 'encoding': 'cp1251'}),
        'flu_data': ('csv', '', ['', '', ''],
                     {'sep': ';', 'low_memory': False, 'dtype': 'str', 'encoding': 'cp1251'}),
        'ln_data': ('csv', 'ЛН', ['Номер', 'ЭЛН', 'Дубликат'],
                    {'sep': ';', 'low_memory': False, 'dtype': 'str', 'encoding': 'cp1251'}),
        'obrdoc_data': ('csv', 'обращений', ['Фамилия', 'Имя', 'Отчество'],
                        {'sep': ';', 'low_memory': False, 'dtype': 'str', 'encoding': 'cp1251'}),
        'obrproc_data': ('csv', 'процедур', ['Фамилия', 'Имя', 'Отчество'],
                         {'sep': ';', 'low_memory': False, 'dtype': 'str', 'encoding': 'cp1251'}),
        'slotepgu1_data': (
            'csv', 'слоты на ЕГПУ', ['Наименование МО', 'Обособленное подразделение', 'Наименование должности'],
            {'sep': ';', 'low_memory': False, 'dtype': 'str', 'encoding': 'cp1251'}),
        'slotepgu14_data': (
            'csv', 'слоты на ЕГПУ', ['Наименование МО', 'Обособленное подразделение', 'Наименование должности'],
            {'sep': ';', 'low_memory': False, 'dtype': 'str', 'encoding': 'cp1251'})
    },
    'oms': {
        'detailed_data': ('csv', 'детализации диспансеризации', ['Номер талона', 'Счет', 'Дата выгрузки'],
                          {'sep': ';', 'low_memory': False, 'na_values': '-', 'dtype': 'str'}),
        'doctors_oms_data': ('csv', 'врачей', ['СНИЛС:', 'Код врача:', 'Фамилия:'],
                             {'sep': ';', 'low_memory': False, 'na_values': '-', 'dtype': 'str'}),
        'oms_data': ('csv', 'ОМС', ['Талон', 'Источник', 'ID источника'],
                     {'sep': ';', 'low_memory': False, 'na_values': '-', 'dtype': 'str'})
    }
}


@file_loader_bp.route('/it/files_loader')
def index():
    data = []
    current_date = datetime.now().strftime('%Y-%m-%d')
    for main_dir, sub_dirs in file_info.items():
        main_dir_path = os.path.join(BASE_DIR, main_dir)
        if os.path.isdir(main_dir_path):
            for sub_dir, (ext, file_type, headers, read_params) in sub_dirs.items():
                sub_dir_path = os.path.join(main_dir_path, sub_dir)
                if os.path.isdir(sub_dir_path):
                    files = os.listdir(sub_dir_path)
                    if files:
                        last_file = files[-1]
                        last_file_path = os.path.join(sub_dir_path, last_file)
                        creation_time = os.path.getctime(last_file_path)
                        creation_time_str = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        last_file = 'No files'
                        creation_time_str = ''
                    data.append((main_dir, sub_dir, last_file, creation_time_str, ext, file_type))
    return render_template('file_loader.html', data=data, current_date=current_date)


@file_loader_bp.route('/upload', methods=['POST'])
def upload():
    main_dir = request.form['main_dir']
    sub_dir = request.form['sub_dir']
    file = request.files['file']
    if file:
        ext, file_type, expected_headers, read_params = file_info[main_dir][sub_dir]
        timestamp = datetime.now().strftime('%Y-%m-%d %H_%M')
        new_filename = f'Выгрузка {file_type} на {timestamp}.{ext}'

        # Сохранение временного файла для проверки
        temp_path = os.path.join(BASE_DIR, 'temp', file.filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        file.save(temp_path)

        df = pd.DataFrame()
        # Проверка заголовков
        if ext == 'csv':
            df = pd.read_csv(temp_path, **read_params)
        elif ext == 'xlsx':
            df = pd.read_excel(temp_path, **read_params)

        if list(df.columns[:3]) == expected_headers:
            save_path = os.path.join(BASE_DIR, main_dir, sub_dir, new_filename)
            os.rename(temp_path, save_path)
            flash('Файл успешно загружен и проверен.', 'success')
        else:
            os.remove(temp_path)
            flash(f'Ошибка: Первые три заголовка файла не соответствуют ожидаемым значениям для {sub_dir}.', 'error')

    return redirect(url_for('file_loader.index'))
