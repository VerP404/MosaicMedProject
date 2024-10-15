# from datetime import datetime
#
# import pandas as pd
# from sqlalchemy import create_engine, text
# from config.settings import DATABASES
#
# # Настройка подключения к базе данных
# postgres_settings = DATABASES['default']
# engine = create_engine(
#     f'postgresql://{postgres_settings["USER"]}:{postgres_settings["PASSWORD"]}@{postgres_settings["HOST"]}:{postgres_settings["PORT"]}/{postgres_settings["NAME"]}'
# )
#
#
# def time_it(method):
#     def timed(*args, **kw):
#         start_time = datetime.now()
#         print(f"Начало '{method.__name__}' в {start_time}")
#         result = method(*args, **kw)
#         end_time = datetime.now()
#         elapsed_time = end_time - start_time
#         print(f"Завершение '{method.__name__}' в {end_time}. Время выполнения: {elapsed_time}")
#         return result
#
#     return timed
#
#
# class DataLoader:
#     def __init__(self,
#                  engine,
#                  table_name,
#                  data_type_name,
#                  column_check,
#                  columns_for_update,
#                  file_format='csv',
#                  sep=';',
#                  dtype='str',
#                  encoding='utf-8'
#                  ):
#         """
#         Инициализация загрузчика данных.
#
#         :param engine: SQLAlchemy engine для подключения к базе данных
#         :param table_name: Название таблицы, в которую будут загружены данные.
#         :param data_type_name: Экземпляр модели DataType, для которого выполняется загрузка данных (ОМС, Квазар и тд).
#                           Смотреть в админке.
#         :param column_check: Название столбца для проверки на null, чтобы убрать ошибки чтения файла
#         :param columns_for_update: Список столбцов для поиска в df и таблице, чтобы обновить строки
#         :param file_format: Формат файла (по умолчанию CSV)
#         :param sep: Разделитель для CSV файлов (по умолчанию ; )
#         :param dtype: Тип данных для чтения (по умолчанию строки)
#         :param encoding: Кодировка для чтения (по умолчанию cp1251)
#         """
#         self.engine = engine
#         self.table_name = table_name
#         self.data_type_name = data_type_name
#         self.columns_mapping = self._get_columns_mapping()
#         self.column_check = column_check
#         self.columns_for_update = columns_for_update
#         self.file_format = file_format
#         self.sep = sep
#         self.dtype = dtype
#         self.encoding = encoding
#         # Инициализируем переменные для статистики
#         self.added_count = 0
#         self.updated_count = 0
#         self.error_count = 0
#
#     @time_it
#     def load_data(self, file_path):
#         """
#         Основной метод для загрузки данных из файла в таблицу.
#         :param file_path: Путь к файлу
#         """
#         total_start_time = datetime.now()
#
#         # Шаг 1: Загрузка данных
#         df = self._load_file_to_df(file_path)
#         print(f"Файл загружен. Количество строк: {df.shape[0]}")
#
#         # Проверка столбцов
#         self._check_columns(df)
#
#         # Шаг 2: Переименование столбцов
#         self._rename_columns(df)
#
#         # Шаг 3: Обработка DataFrame
#         df = self._process_dataframe(df)
#
#         # Шаг 4: Удаление существующих строк по уникальному столбцу
#         self._delete_existing_rows(df)
#
#         # Шаг 5: Загрузка данных в базу
#         self._load_data_to_db(df)
#
#         # Шаг 6: Создаем запись в DataImport
#         self._create_data_import_record()
#
#         # Финальное время
#         total_end_time = datetime.now()
#         elapsed_time = total_end_time - total_start_time
#         print(f"Общее время выполнения: {elapsed_time}")
#
#     @time_it
#     def _get_columns_mapping(self):
#         """
#         Загружает соответствия столбцов для типа данных через SQL запрос, основываясь на имени типа данных.
#         """
#         sql_query = """
#             SELECT fm.csv_column_name, fm.model_field_name
#             FROM data_loader_datatypefieldmapping fm
#             JOIN data_loader_datatype dt ON fm.data_type_id = dt.id
#             WHERE dt.name = :data_type_name
#         """
#
#         # Выполняем SQL запрос и возвращаем результат как список кортежей
#         with self.engine.connect() as connection:
#             result = connection.execute(text(sql_query), {'data_type_name': self.data_type_name}).fetchall()
#
#         # Преобразуем результат запроса в словарь {csv_column_name: model_field_name}
#         columns_mapping = {row[0]: row[1] for row in result}  # Используем индексы вместо строк
#         print(f"Сопоставление столбцов загружено: {columns_mapping}")
#         return columns_mapping
#
#     @time_it
#     def _load_file_to_df(self, file_path):
#         """Загрузка файла в DataFrame."""
#         print(f"Начата загрузка файла {file_path}")
#         if self.file_format == 'csv':
#             df = pd.read_csv(file_path, sep=self.sep, low_memory=False, na_values="-", dtype=self.dtype,
#                              encoding=self.encoding)
#         elif self.file_format == 'excel':
#             df = pd.read_excel(file_path)
#         else:
#             raise ValueError("Неподдерживаемый формат файла")
#         print(f"Файл {file_path} успешно загружен. Размер данных: {df.shape}")
#         return df
#
#     @time_it
#     def _check_columns(self, df):
#         """
#         Проверяет наличие и соответствие столбцов.
#         """
#         print("Проверка соответствия столбцов...")
#         file_columns = set(df.columns)
#         expected_columns = set(self.columns_mapping.keys())
#
#         missing_columns = expected_columns - file_columns
#         extra_columns = file_columns - expected_columns
#
#         if missing_columns or extra_columns:
#             if missing_columns:
#                 print(f"Отсутствующие столбцы: {missing_columns}")
#             if extra_columns:
#                 print(f"Лишние столбцы: {extra_columns}")
#             raise ValueError("Структура файла не соответствует ожиданиям.")
#         print("Все необходимые столбцы присутствуют.")
#
#     @time_it
#     def _rename_columns(self, df):
#         """
#         Переименовывает столбцы DataFrame на основе словаря.
#         """
#         print("Переименование столбцов...")
#         df.rename(columns=self.columns_mapping, inplace=True)
#         print("Столбцы переименованы.")
#
#     @time_it
#     def _process_dataframe(self, df):
#         """
#         Обрабатывает DataFrame: удаляет NaN и преобразует данные в строки.
#         """
#         print("Обработка данных DataFrame...")
#         try:
#             # Удаляем строки, содержащие NaN на основании столбца column_check
#             df.dropna(subset=[self.column_check], inplace=True)
#         except KeyError as e:
#             print(f"Ошибка: столбец '{self.column_check}' не найден в данных. Проверьте наличие столбца в базе.")
#             print(f"Доступные столбцы: {list(df.columns)}")
#             raise e  # Повторное возбуждение исключения для остановки выполнения, если необходимо
#
#         # Заменяем NaN на '-' в датафрейме
#         df.fillna('-', inplace=True)
#
#         # Убираем ` из датафрейма при наличии
#         df = df.replace('`', '', regex=True)
#
#         # Удаляем неразрывные пробелы (NBSP) и заменяем их на обычные пробелы
#         df.replace('\u00A0', ' ', regex=True, inplace=True)
#
#         # Проверяем что тип данных у всех столбцов "текстовый"
#         df = df.astype(str)
#
#         print("Обработка данных завершена.")
#         return df
#
#     @time_it
#     def _delete_existing_rows(self, df):
#         """
#         Удаляет строки из базы данных, если значения в столбцах из columns_for_update совпадают между DataFrame и базой данных.
#         """
#         print("Начат процесс удаления существующих строк из базы данных...")
#         try:
#             # Приводим значения всех столбцов в DataFrame к строковому типу, если они еще не строки
#             for column in self.columns_for_update:
#                 df[column] = df[column].astype(str)
#
#             # Создаем список уникальных комбинаций ключей из DataFrame
#             keys_in_df = df[self.columns_for_update].drop_duplicates()
#
#             # Формируем условие для SQL-запроса
#             conditions = ' OR '.join([
#                 '(' + ' AND '.join([f"{col} = :{col}_{i}" for col in self.columns_for_update]) + ')'
#                 for i in range(len(keys_in_df))
#             ])
#
#             # Подготавливаем параметры для запроса
#             params = {}
#             for idx, row in keys_in_df.iterrows():
#                 for col in self.columns_for_update:
#                     params[f"{col}_{idx}"] = row[col]
#
#             if conditions:
#                 delete_query = text(f"DELETE FROM {self.table_name} WHERE {conditions}")
#                 with self.engine.begin() as connection:
#                     connection.execute(delete_query, params)
#                 print(f"Удалены существующие строки по ключам: {self.columns_for_update}")
#             else:
#                 print("Нет существующих строк для удаления.")
#
#         except Exception as e:
#             print(f"Ошибка при удалении существующих строк: {e}")
#
#     @time_it
#     def _load_data_to_db(self, df):
#         """
#         Загружает данные в базу данных с отслеживанием прогресса.
#         """
#         print("Начата загрузка данных в базу данных...")
#         # Удаляем столбец combined_key, который используется только для внутренней обработки
#         if 'combined_key' in df.columns:
#             df.drop(columns=['combined_key'], inplace=True)
#
#         total_rows = df.shape[0]
#         loaded_rows = 0
#         try:
#             for chunk_start in range(0, total_rows, 1000):
#                 chunk = df.iloc[chunk_start:chunk_start + 1000]
#                 chunk.to_sql(
#                     name=self.table_name,
#                     con=self.engine,
#                     if_exists='append',
#                     index=False,
#                     method='multi'
#                 )
#                 loaded_rows += chunk.shape[0]
#                 self.added_count += chunk.shape[0]
#                 print(f"Загружено {loaded_rows} строк из {total_rows}.")
#         except Exception as e:
#             self.error_count += 1
#             print(f"Ошибка при загрузке данных: {e}")
#
#     @time_it
#     def _create_data_import_record(self):
#         """
#         Создает запись в таблице DataImport с информацией о загрузке через SQL-запрос.
#         """
#         print("Создание записи о загрузке данных в таблице DataImport...")
#         sql_query = """
#         INSERT INTO data_loader_dataimport (csv_file, date_added, added_count, updated_count, error_count, data_type_id)
#         VALUES (:csv_file, NOW(), :added_count, :updated_count, :error_count, :data_type_id)
#         """
#
#         with self.engine.begin() as connection:
#             data_type_query = "SELECT id FROM data_loader_datatype WHERE name = :data_type_name"
#             print(f"Поиск data_type_id для '{self.data_type_name}'")
#             data_type_id_result = connection.execute(
#                 text(data_type_query),
#                 {'data_type_name': self.data_type_name}
#             ).fetchone()
#
#             if data_type_id_result:
#                 data_type_id = data_type_id_result[0]
#                 print(f"Тип данных найден, ID: {data_type_id}")
#                 try:
#                     # Выполняем основной запрос, используя фактический data_type_id
#                     connection.execute(text(sql_query), {
#                         'csv_file': '-',  # Укажите путь к файлу или значение
#                         'added_count': self.added_count,
#                         'updated_count': self.updated_count,
#                         'error_count': self.error_count,
#                         'data_type_id': data_type_id
#                     })
#                     print("Запись в таблице DataImport успешно создана.")
#                 except Exception as e:
#                     print(f"Ошибка при вставке записи в DataImport: {e}")
#             else:
#                 print(f"Ошибка: Тип данных с именем '{self.data_type_name}' не найден.")
#
#
# if __name__ == "__main__":
#     # file_path = fr"C:\DjangoProject\MosaicMedProject\journal_20240917(1).csv"
#     # file_path = fr"C:\Users\frdro\Downloads\Telegram Desktop\journal_20241004(2).csv"
#     # file_path = fr"C:\Users\frdro\Downloads\Telegram Desktop\journal_Detailed_Medical_Examination_20241006.csv"
#     # file_path = fr"C:\Users\frdro\Downloads\Telegram Desktop\journal_Doctors_20241006.csv"
#     # file_path = fr"C:\Users\RDN\Downloads\Att_MO_36002520241008.csv"
#     file_path = fr"C:\Users\RDN\Downloads\Report - 2024-10-08T091240.678.csv"
#
#     loader = DataLoader(engine=engine,
#                         table_name="data_loader_iszldisnabjob",
#                         data_type_name='disnabjob',
#                         column_check="id_iszl",
#                         columns_for_update=['id_iszl', 'enp', 'ds'],
#                         encoding='cp1251'
#                         )
#     loader.load_data(file_path)
#
# #                         table_name="data_loader_iszldisnabjob",
# #                         data_type_name='disnabjob',
# #                         column_check="id_iszl",
# #                         columns_for_update=['id_iszl', 'enp', 'ds' ],
# #                         encoding='cp1251'
#
# #                         table_name="data_loader_iszldisnab",
# #                         data_type_name='disnab',
# #                         column_check="pdwid",
# #                         columns_for_update=['pdwid'],
# #                         encoding='cp1251'
#
# #                         table_name = "data_loader_iszlpeople",
# #                         data_type_name = 'people',
# #                         column_check = "enp",
# #                         columns_for_update = ['enp'],
#
# #                         table_name = "data_loader_omsdata",
# #                         data_type_name = 'OMS',
# #                         column_check = "patient",
# #                         columns_for_update = ['talon'],
