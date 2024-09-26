import os
import platform
from dash import html, dcc, Input, Output, State
import subprocess
import dash_bootstrap_components as dbc
from sqlalchemy.exc import ProgrammingError
from services.MosaicMed.app import app
from services.MosaicMed.callback.callback import query_last_record_sql, last_file_csv_in_directory

# Определяем базовый путь к скриптам и папкам
script_dir = os.path.dirname(os.path.abspath(__file__))
base_script_path = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'database', 'to_database'))

# Определяем путь к интерпретатору Python в зависимости от операционной системы
if platform.system() == 'Windows':
    venv_python = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', '.venv', 'Scripts', 'python.exe'))
else:
    venv_python = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', '.venv', 'bin', 'python'))

file_paths = {
    'oms': os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'files', 'oms', 'oms_data')),
    'people': os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'files', 'iszl', 'people_data')),
    'iszl': os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'files', 'iszl', 'iszl_data')),
    'emd': os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'files', 'kvazar', 'emd_data')),
    'doctors': os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'files', 'oms', 'doctors_oms_data')),
    'area': os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'files', 'info', 'area_data')),
    'dn168n': os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'files', 'info', 'dn168n_data')),
    'obrprocedur': os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'files', 'kvazar', 'obrproc_data')),
    'detailed': os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'files', 'oms', 'detailed_data')),
    'ln': os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'files', 'kvazar', 'ln_data')),
    'obrdoc': os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..', '..', 'files', 'kvazar', 'obrdoc_data'))
}

schema_names = {
    'oms': 'oms',
    'doctors': 'oms',
    'detaildd': 'oms',
    'area': 'info',
    'dn168n': 'info',
    'naselenie': 'info',
    'iszl': 'iszl',
    'people': 'iszl',
    'emd': 'kvazar',
    'flu': 'kvazar',
    'ln': 'kvazar',
    'obrdoc': 'kvazar',
    'obrproc': 'kvazar',
}

type_page = "update-bd"

# Функция для создания компонента обновления файла
def create_update_file_component(index, title, path_script):
    return html.Div(
        [
            html.H3(f'{index}. {title}', className='label'),
            html.P(id=f"file{index}-in-bd"),
            html.P(id=f"file{index}-for-bd"),
            dbc.Alert(id=f'color-indicator{index}', color="primary"),
            dbc.Button('Запустить скрипт', id=f'run-script{index}-button-{type_page}'),
            html.Div(id=f'script{index}-output-{type_page}'),
            dcc.Loading(id=f"loading{index}-output-{type_page}", children=[], type="default"),
            html.Hr()
        ]
    )

# Определение страницы
tab_layout_it_update_bd = html.Div(
    [
        html.Div(
            [
                dbc.Button('Проверить актуальность файлов', id='run-script-button'),
                html.Hr(),
                create_update_file_component(1, 'Обновление файла ОМС', os.path.join(base_script_path, 'oms_to_database.py')),
                create_update_file_component(2, 'Обновление файла населения из ИСЗЛ', os.path.join(base_script_path, 'people_to_database.py')),
                create_update_file_component(3, 'Обновление файла диспансерного наблюдения из ИСЗЛ', os.path.join(base_script_path, 'iszl_to_database.py')),
                create_update_file_component(4, 'Обновление файла ЭМД из Квазар', os.path.join(base_script_path, 'emd_to_database.py')),
                create_update_file_component(5, 'Обновление файла врачей из Web.ОМС', os.path.join(base_script_path, 'doctors_oms_to_database.py')),
                create_update_file_component(6, 'Обновление списка участковых врачей и участков', os.path.join(base_script_path, 'area_to_database.py')),
                create_update_file_component(7, 'Обновление списка диагнозов и специальностей по 168н', os.path.join(base_script_path, '168n_to_database.py')),
                create_update_file_component(8, 'Обновление списка записанных на процедуры из журнала обращений Квазар', os.path.join(base_script_path, 'obrprocedur_to_database.py')),
                create_update_file_component(9, 'Обновление детализации диспансеризации', os.path.join(base_script_path, 'detailed_dd_to_database.py')),
                create_update_file_component(10, 'Обновление листов нетрудоспособности', os.path.join(base_script_path, 'ln_to_database.py')),
                create_update_file_component(11, 'Обновление журнала обращений', os.path.join(base_script_path, 'obrdoc_to_database.py')),
            ]
        )
    ]
)

# Функция для выполнения скрипта
def run_script(n_clicks, loading_children, script_output_children, path_script):
    if n_clicks is None:
        return [], "Нажмите кнопку, чтобы запустить скрипт."

    if not loading_children:
        if not os.path.exists(path_script):
            return [], f"Файл не найден: {path_script}"

        if not os.path.exists(venv_python):
            return [], f"Python не найден: {venv_python}"

        try:
            result = subprocess.run(
                [venv_python, path_script],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            decoded_text = result.stdout.encode('cp1251').decode('utf-8', errors='ignore')
            return [], f"Результат выполнения скрипта:\n{decoded_text}"
        except subprocess.CalledProcessError as e:
            return [], f"Ошибка при выполнении скрипта:\n{e.output}"

    return "Выполняется скрипт, подождите...", script_output_children

# Функция для создания callback'ов
def create_script_callback(index, path_script):
    @app.callback(
        [Output(f'loading{index}-output-{type_page}', 'children'),
         Output(f'script{index}-output-{type_page}', 'children')],
        [Input(f'run-script{index}-button-{type_page}', 'n_clicks')],
        [State(f'loading{index}-output-{type_page}', 'children'),
         State(f'script{index}-output-{type_page}', 'children')]
    )
    def run_script_callback(n_clicks, loading_children, script_output_children):
        return run_script(n_clicks, loading_children, script_output_children, path_script)

# Создание всех необходимых callback'ов
create_script_callback(1, os.path.join(base_script_path, 'oms_to_database.py'))
create_script_callback(2, os.path.join(base_script_path, 'people_to_database.py'))
create_script_callback(3, os.path.join(base_script_path, 'iszl_to_database.py'))
create_script_callback(4, os.path.join(base_script_path, 'emd_to_database.py'))
create_script_callback(5, os.path.join(base_script_path, 'doctors_oms_to_database.py'))
create_script_callback(6, os.path.join(base_script_path, 'area_to_database.py'))
create_script_callback(7, os.path.join(base_script_path, '168n_to_database.py'))
create_script_callback(8, os.path.join(base_script_path, 'obr_procedur_to_database.py'))
create_script_callback(9, os.path.join(base_script_path, 'detailed_dd_to_database.py'))
create_script_callback(10, os.path.join(base_script_path, 'ln_to_database.py'))
create_script_callback(11, os.path.join(base_script_path, 'obr_doc_to_database.py'))

@app.callback(
    [Output(f'color-indicator{i}', 'color') for i in range(1, 12)],
    [Input('run-script-button', 'n_clicks')]
)
def update_color_indicator(n_clicks):
    def indicator_files(n_click, file_in_bd, file_for_bd):
        if n_click is None:
            return ''
        if file_in_bd == file_for_bd:
            return "success"
        return "danger"

    try:
        return tuple(
            indicator_files(
                n_clicks,
                query_last_record_sql(schema_names[log_name.split('_')[0]], log_name),
                last_file_csv_in_directory(file_path)[0]  # Используем только первый элемент кортежа
            )
            for log_name, file_path in zip(
                ['oms_log', 'people_log', 'iszl_log', 'emd_log', 'doctors_oms_log', 'area_log', 'dn168n_log', 'obrproc_log', 'detaildd_log', 'ln_log', 'obrproc_log'],
                list(file_paths.values())
            )
        )
    except ProgrammingError as e:
        return tuple("danger" for _ in range(11))

@app.callback(
    [Output(f"file{i}-in-bd", "children") for i in range(1, 12)] +
    [Output(f"file{i}-for-bd", "children") for i in range(1, 12)],
    [Input('run-script-button', 'n_clicks')]
)
def update_text(n_clicks):
    try:
        return tuple(
            f"Последний файл загруженный в БД: {query_last_record_sql(schema_names[log_name.split('_')[0]], log_name)}" for log_name in
            ['oms_log', 'people_log', 'iszl_log', 'emd_log', 'doctors_oms_log', 'area_log', 'dn168n_log', 'obrproc_log', 'detaildd_log', 'ln_log', 'obrproc_log']
        ) + tuple(
            f"Последний файл для загрузки в БД: {last_file_csv_in_directory(file_path)[0] or 'Нет файла в папке'}" for file_path in list(file_paths.values())
        )
    except ProgrammingError as e:
        return tuple(f"Ошибка: {str(e)}" for _ in range(22))

