import pandas as pd
import os

# Словари перетащить в отдельный справочный файл
uch = {'ГП3': ['012_360025', '013_360025', '014_360025', '015_360025', '016_360025', '017_360025', '018_360025',
               '019_360025', '020_360025', '021_360025', '022_360025', '023_360025', '026_360025', '027_360025',
               '029_360025', '032_360025', '033_360025', '034_360025', '035_360025'],
       'ОАПП1': ['000_360025', '001_360025', '002_360025', '003_360025', '004_360025', '005_360025', '006_360025',
                 '007_360025', '008_360025', '009_360025', '010_360025', '011_360025'],
       'ОАПП2': ['024_360025', '025_360025', '028_360025', '030_360025', '031_360025'],
       'ГП11': ['000_360101', '001_360101', '002_360101', '003_360101', '004_360101', '005_360101', '006_360101',
                '007_360101', '008_360101', '009_360101', '010_360101', '011_360101', '012_360101', '013_360101',
                '014_360101', '015_360101', '016_360101', '017_360101', '018_360101', '019_360101'],
       'ДП1': ['001_360026', '002_360026', '003_360026', '004_360026', '005_360026', '006_360026', '007_360026',
               '008_360026', '009_360026', '010_360026', '011_360026', '012_360026', '013_360026', '014_360026',
               '015_360026', '016_360026'],
       'ДП8': ['001_360027', '002_360027', '003_360027', '004_360027', '005_360027', '006_360027', '007_360027',
               '008_360027', '009_360027', '010_360027', '011_360027', '012_360027', '013_360027', '014_360027',
               '015_360027']
       }
diagnosis_groups = {
    'i60-i69': ['I60', 'I61', 'I62', 'I63', 'I64', 'I65', 'I66', 'I67', 'I68', 'I69'],
    'i60-i64': ['I60', 'I61', 'I62', 'I63', 'I64'],
    'i21-i22': ['I21', 'I22'],
    'i10-i13': ['I10', 'I11', 'I12', 'I13'],
    'i20-i25': ['I20', 'I21', 'I22', 'I23', 'I24', 'I25'],
    'Е10-Е14': ['E10', 'E11', 'E12', 'E13', 'E14'],
    'C00-C97': ['C00', 'C01', 'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09', 'C10', 'C11',
                'C12', 'C13', 'C14', 'C15', 'C16', 'C17', 'C18', 'C19', 'C20', 'C21', 'C22', 'C23',
                'C24', 'C25', 'C26', 'C27', 'C28', 'C29', 'C30', 'C31', 'C32', 'C33', 'C34', 'C35',
                'C36', 'C37', 'C38', 'C39', 'C40', 'C41', 'C42', 'C43', 'C44', 'C45', 'C46', 'C47',
                'C48', 'C49', 'C50', 'C51', 'C52', 'C53', 'C54', 'C55', 'C56', 'C57', 'C58', 'C59',
                'C60', 'C61', 'C62', 'C63', 'C64', 'C65', 'C66', 'C67', 'C68', 'C69', 'C70', 'C71',
                'C72', 'C73', 'C74', 'C75', 'C76', 'C77', 'C78', 'C79', 'C80', 'C81', 'C82', 'C83',
                'C84', 'C85', 'C86', 'C87', 'C88', 'C89', 'C90', 'C91', 'C92', 'C93', 'C94', 'C95',
                'C96', 'C97'],
    'A15-A19': ['A15', 'A16', 'A17', 'A18', 'A19'],
    'J00-J99': ['J00', 'J01', 'J02', 'J03', 'J04', 'J05', 'J06', 'J07', 'J08', 'J09', 'J10', 'J11',
                'J12', 'J13', 'J14', 'J15', 'J16', 'J17', 'J18', 'J20', 'J21', 'J22', 'J30', 'J31',
                'J32', 'J33', 'J34', 'J35', 'J36', 'J37', 'J38', 'J39', 'J40', 'J41', 'J42', 'J43',
                'J44', 'J45', 'J46', 'J47', 'J60', 'J61', 'J62', 'J63', 'J64', 'J65', 'J66', 'J67',
                'J68', 'J69', 'J70', 'J80', 'J81', 'J82', 'J84', 'J85', 'J86', 'J90', 'J91', 'J92',
                'J93', 'J94', 'J95', 'J96', 'J98', 'J99'],
    'J44-J47': ['J44', 'J45', 'J46', 'J47'],
    'J12-J18': ['J12', 'J13', 'J14', 'J15', 'J16', 'J17', 'J18'],
    'k00-k93': ['K00', 'K01', 'K02', 'K03', 'K04', 'K05', 'K06', 'K07', 'K08', 'K09', 'K10', 'K11',
                'K12', 'K13', 'K14', 'K20', 'K21', 'K22', 'K23', 'K25', 'K26', 'K27', 'K28', 'K29',
                'K30', 'K31', 'K35', 'K36', 'K37', 'K38', 'K39', 'K40', 'K41', 'K42', 'K43', 'K44',
                'K45', 'K46', 'K50', 'K51', 'K52', 'K55', 'K56', 'K57', 'K58', 'K59', 'K60', 'K61',
                'K62', 'K63', 'K65', 'K66', 'K67', 'K70', 'K71', 'K72', 'K73', 'K74', 'K75', 'K76',
                'K80', 'K81', 'K82', 'K83', 'K85', 'K86', 'K87', 'K90', 'K91', 'K92', 'K93'],
    's00-t98': ['S00', 'S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08', 'S09', 'S10', 'S11',
                'S12', 'S13', 'S14', 'S15', 'S16', 'S17', 'S18', 'S19', 'S20', 'S21', 'S22', 'S23',
                'S24', 'S25', 'S26', 'S27', 'S28', 'S29', 'S30', 'S31', 'S32', 'S33', 'S34', 'S35',
                'S36', 'S37', 'S38', 'S39', 'S40', 'S41', 'S42', 'S43', 'S44', 'S45', 'S46', 'S47',
                'S48', 'S49', 'S50', 'S51', 'S52', 'S53', 'S54', 'S55', 'S56', 'S57', 'S58', 'S59',
                'S60', 'S61', 'S62', 'S63', 'S64', 'S65', 'S66', 'S67', 'S68', 'S69', 'S70', 'S71',
                'S72', 'S73', 'S74', 'S75', 'S76', 'S77', 'S78', 'S79', 'S80', 'S81', 'S82', 'S83',
                'S84', 'S85', 'S86', 'S87', 'S88', 'S89', 'S90', 'S91', 'S92', 'S93', 'S94', 'S95',
                'S96', 'S97', 'T00', 'T01', 'T02', 'T03', 'T04', 'T05', 'T06', 'T07', 'T08', 'T09',
                'T10', 'T11', 'T12', 'T13', 'T14', 'T15', 'T16', 'T17', 'T18', 'T19', 'T20', 'T21',
                'T22', 'T23', 'T24', 'T25', 'T26', 'T27', 'T28', 'T29', 'T30', 'T31', 'T32', 'T33',
                'T34', 'T35', 'T36', 'T37', 'T38', 'T39', 'T40', 'T41', 'T42', 'T43', 'T44', 'T45',
                'T46', 'T47', 'T48', 'T49', 'T50', 'T51', 'T52', 'T53', 'T54', 'T55', 'T56', 'T57',
                'T58', 'T59', 'T60', 'T61', 'T62', 'T63', 'T64', 'T65', 'T66', 'T67', 'T68', 'T69',
                'T70', 'T71', 'T72', 'T73', 'T74', 'T75', 'T76', 'T77', 'T78', 'T79', 'T80', 'T81',
                'T82', 'T83', 'T84', 'T85', 'T86', 'T87', 'T88', 'T89', 'T90', 'T91', 'T92', 'T93',
                'T94', 'T95', 'T96', 'T97', 'T98']
}


def neotlojka_data(df_, patient_file):
    # Загружаем и обрабатываем файл ЭПМЗ и населения
    def load_data(df, path_patient):
        df_epmz = df
        df_epmz = df_epmz[(df_epmz['Тип ЭПМЗ'] == 'Амбулаторный случай') &
                          (df_epmz[
                               'Цель обслуживания'] == '22 - Посещение по неотложной медицинской помощи, '
                                                       'оказанной  службой неотложной помощи, созданной '
                                                       'на базе амбулаторно-поликлинической службы')]
        df_epmz['Диагноз'] = df_epmz['Диагноз'].str.slice(0, 3)

        df_naselenie = pd.read_csv(path_patient, sep=';', dtype='str', encoding='utf-8')
        df_naselenie['ENP'] = df_naselenie['ENP'].apply(lambda x: x.replace('`', '') if isinstance(x, str) else x)
        # Формируем сводную таблицу
        df_merge_data = df_epmz.merge(df_naselenie, left_on='ЕНП', right_on='ENP', how='left')[
            ['Диагноз', 'ЕНП', 'LPUUCH']]

        # функция проверяет правильность участка и если такого участка нет, то пишет 'другой'
        def check_uch(row):
            for key, value in uch.items():
                if row['LPUUCH'] in value:
                    return key
            return 'другой'

        df_merge_data['Корпус'] = df_merge_data.apply(check_uch, axis=1)
        df_merge_data['LPUUCH'] = df_merge_data['LPUUCH'].fillna('нет')
        df_merge_data['Корпус'] = df_merge_data['Корпус'].apply(lambda x: x.replace('ОАПП1', 'ОАПП1 ГП3') if isinstance(x, str) else x)
        df_merge_data['Корпус'] = df_merge_data['Корпус'].apply(lambda x: x.replace('ОАПП2', 'ОАПП2 ГП3') if isinstance(x, str) else x)

        return df_merge_data

    def counts_data(df):
        # Создание пустого словаря для хранения подсчета
        counts_dat = {}

        # Итерация по каждому участку (LPUUCH)
        for uchast in df['LPUUCH'].unique():
            uch_data = df[df['LPUUCH'] == uchast]  # Фильтрация данных по участку

            # Получение значения столбца "Корпус" для данного участка
            korpus = uch_data['Корпус'].iloc[0]

            # Создание пустого словаря для хранения подсчета групп диагнозов
            group_counts = {}

            # Итерация по каждой группе диагнозов
            for group, diagnoses in diagnosis_groups.items():
                group_data = uch_data[uch_data['Диагноз'].isin(diagnoses)]  # Фильтрация данных по группе диагнозов
                group_count = len(group_data)  # Подсчет количества записей в группе
                group_counts[group] = group_count  # Добавление количества в словарь

            # Подсчет количества записей, которых нет в словаре
            other_count = len(uch_data) - sum(group_counts.values())

            group_counts['Другие'] = other_count  # Добавление количества других записей в словарь
            group_counts['Корпус'] = korpus  # Добавление значения столбца "Корпус" в словарь
            group_counts['Итого'] = len(uch_data)  # Общее количество записей для участка

            counts_dat[uchast] = group_counts  # Добавление словаря подсчета групп диагнозов в словарь подсчета участка
        return counts_dat

    def counts_in_df(counts_d):
        # Преобразование словаря подсчета в датафрейм
        counts_df_data = pd.DataFrame(counts_d).T
        counts_df_data['Участок'] = counts_df_data.index
        # Переупорядочивание столбцов
        counts_df_data = counts_df_data[['Корпус', 'Участок'] + list(diagnosis_groups.keys()) + ['Другие', 'Итого']]
        # Суммирование участков с Корпусом "другой"
        df_other_data = counts_df_data[counts_df_data['Корпус'] == 'другой'].groupby('Корпус').sum().reset_index()
        df_other_data['Участок'] = 'Другой'
        # Объединение результатов
        counts_df_data = pd.concat([counts_df_data[counts_df_data['Корпус'] != 'другой'], df_other_data])
        # Сортировка по столбцам "Корпус" и "Участок"
        counts_df_data = counts_df_data.sort_values(by=['Корпус', 'Участок'])
        # Обновление индекса
        counts_df_data = counts_df_data.reset_index(drop=True)

        # Добавляем строку с суммой по ГП11
        summ_korp = counts_df_data[counts_df_data['Корпус'] == 'ГП11']
        count_summ_korp = summ_korp.sum()
        counts_df_data = pd.concat([counts_df_data, pd.DataFrame([count_summ_korp], columns=counts_df_data.columns)],
                                   ignore_index=True)
        counts_df_data.loc[counts_df_data.index[-1], 'Корпус'] = 'ГП11'
        counts_df_data.loc[counts_df_data.index[-1], 'Участок'] = 'Итого'

        # Добавляем строку с суммой по ГП3/ОАПП1/ОАПП2
        summ_korp = counts_df_data[(counts_df_data['Корпус'] == 'ГП3') |
                                   (counts_df_data['Корпус'] == 'ОАПП1 ГП3') |
                                   (counts_df_data['Корпус'] == 'ОАПП2 ГП3')]
        count_summ_korp = summ_korp.sum()
        counts_df_data = pd.concat([counts_df_data, pd.DataFrame([count_summ_korp], columns=counts_df_data.columns)],
                                   ignore_index=True)
        counts_df_data.loc[counts_df_data.index[-1], 'Корпус'] = 'ОАПП + ГП3'
        counts_df_data.loc[counts_df_data.index[-1], 'Участок'] = 'Итого'

        # убираем детские поликлиники
        counts_df_data = counts_df_data[~counts_df_data['Корпус'].str.contains('ДП')]

        return counts_df_data

    path_patient_file = fr'\\10.136.29.166\_it_reports\Download ISZL\people\{patient_file}'

    df_merge = load_data(df_, path_patient_file)
    counts = counts_data(df_merge)
    return counts_in_df(counts)


def neotlojka_pacient_last_file(directory):
    # Получение списка файлов в папке
    files = os.listdir(directory)

    # Фильтрация файлов по расширению .csv
    csv_files = [file for file in files if file.endswith('.csv')]

    # Сортировка файлов по дате изменения в обратном порядке
    sorted_files = sorted(csv_files, key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)

    if sorted_files:
        latest_file = sorted_files[0]
        # date = latest_file.split('_')[1].split('.')[0]  # Извлечение даты из имени файла
        # formatted_date = f'выгрузка от {date[:2]}.{date[2:4]}.{date[4:]}'  # Преобразование даты в нужный формат

        date_str = latest_file[-12:-4]

        formatted_date = "выгрузка от {}.{}.{}".format(date_str[6:], date_str[4:6], date_str[:4])

        return latest_file, formatted_date
    else:
        return 'В папке нет файла населения', 'В папке нет файла населения'
