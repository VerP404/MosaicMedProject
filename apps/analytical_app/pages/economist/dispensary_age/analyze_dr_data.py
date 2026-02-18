#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ данных диспансеризации ДР1 и ДР2
Фильтрация по номенклатурным кодам начинающимся на B
Расчет итоговой стоимости по ЕНП с учетом этапов и группы здоровья
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def load_dr_data():
    """Загрузка данных ДР1 и ДР2"""
    
    print("ЗАГРУЗКА ДАННЫХ ДИСПАНСЕРИЗАЦИИ")
    print("=" * 80)
    
    # Читаем имена файлов из текстового файла
    config_file = Path("file_names.txt")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            file_names = [line.strip() for line in f.readlines() if line.strip()]
        
        if len(file_names) < 2:
            print(f"Ошибка: в файле {config_file} должно быть минимум 2 имени файла")
            return None, None, None
        
        dr1_file = Path(file_names[0])
        dr2_file = Path(file_names[1])
        
        print(f"Файл ДР1: {dr1_file}")
        print(f"Файл ДР2: {dr2_file}")
        
    except FileNotFoundError:
        print(f"Ошибка: файл {config_file} не найден")
        return None, None, None
    except Exception as e:
        print(f"Ошибка при чтении файла {config_file}: {e}")
        return None, None, None
    
    try:
        # Загружаем данные ДР1 (большой файл)
        print(f"Загружаем ДР1: {dr1_file}")
        dr1_df = pd.read_csv(dr1_file, sep=';', encoding='utf-8')
        print(f"ДР1: {dr1_df.shape[0]} строк, {dr1_df.shape[1]} колонок")
        
        # Загружаем данные ДР2 (маленький файл)
        print(f"Загружаем ДР2: {dr2_file}")
        dr2_df = pd.read_csv(dr2_file, sep=';', encoding='utf-8')
        print(f"ДР2: {dr2_df.shape[0]} строк, {dr2_df.shape[1]} колонок")
        
        # Объединяем данные
        combined_df = pd.concat([dr1_df, dr2_df], ignore_index=True)
        print(f"Объединенные данные: {combined_df.shape[0]} строк")
        
        return combined_df, dr1_df, dr2_df
    
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return None, None, None

def analyze_data_structure(df):
    """Анализ структуры данных"""
    
    if df is None:
        return
    
    print("\n" + "=" * 80)
    print("АНАЛИЗ СТРУКТУРЫ ДАННЫХ")
    print("=" * 80)
    
    print(f"Колонки: {list(df.columns)}")
    print(f"Типы данных:")
    print(df.dtypes)
    
    # Анализ типов талонов
    print(f"\nТипы талонов:")
    print(df['Тип талона'].value_counts())
    
    # Анализ номенклатурных кодов
    print(f"\nУникальные номенклатурные коды (первые 20):")
    unique_codes = df['Номенклатурный код услуги'].dropna().unique()
    print(unique_codes[:20])
    
    # Анализ кодов начинающихся на B
    b_codes = df[df['Номенклатурный код услуги'].str.startswith('B', na=False)]
    print(f"\nКоды начинающиеся на B: {len(b_codes)} строк")
    print("Уникальные B коды:")
    print(b_codes['Номенклатурный код услуги'].value_counts())
    
    # Анализ групп здоровья
    print(f"\nГруппы здоровья:")
    print(df['Группа здоровья'].value_counts())
    
    # Анализ направлений на II этап
    stage2_direction = df[df['Группа здоровья'].str.contains('Направлен на II этап', na=False)]
    print(f"\nНаправления на II этап: {len(stage2_direction)} строк")

def filter_b_codes(df):
    """Фильтрация строк с номенклатурными кодами начинающимися на B"""
    
    if df is None:
        return None
    
    print("\n" + "=" * 80)
    print("ФИЛЬТРАЦИЯ ПО КОДАМ НАЧИНАЮЩИМСЯ НА B")
    print("=" * 80)
    
    # Фильтруем строки с кодами начинающимися на B
    b_codes_df = df[df['Номенклатурный код услуги'].str.startswith('B', na=False)].copy()
    
    print(f"Найдено строк с B кодами: {len(b_codes_df)}")
    print(f"Уникальных B кодов: {b_codes_df['Номенклатурный код услуги'].nunique()}")
    
    # Показываем уникальные B коды
    print("\nУникальные B коды:")
    b_code_counts = b_codes_df['Номенклатурный код услуги'].value_counts()
    print(b_code_counts)
    
    # Показываем примеры данных
    print(f"\nПримеры отфильтрованных данных:")
    print(b_codes_df[['Номер талона', 'Тип талона', 'ЕНП', 'Номенклатурный код услуги', 'Название услуги', 'Стоимость']].head(10))
    
    return b_codes_df

def identify_main_services(b_codes_df):
    """Определение основных услуг для каждого номера талона"""
    
    if b_codes_df is None:
        return None
    
    print("\n" + "=" * 80)
    print("ОПРЕДЕЛЕНИЕ ОСНОВНЫХ УСЛУГ")
    print("=" * 80)
    
    # Группируем по номеру талона и находим основную услугу
    main_services = []
    
    for talon_number in b_codes_df['Номер талона'].unique():
        talon_data = b_codes_df[b_codes_df['Номер талона'] == talon_number]
        
        # Берем первую строку как основную услугу (обычно это основная услуга)
        main_service = talon_data.iloc[0].copy()
        main_services.append(main_service)
    
    main_services_df = pd.DataFrame(main_services)
    
    print(f"Найдено основных услуг: {len(main_services_df)}")
    print(f"По типам талонов:")
    print(main_services_df['Тип талона'].value_counts())
    
    return main_services_df

def calculate_patient_costs(main_services_df):
    """Расчет итоговой стоимости по ЕНП с учетом этапов"""
    
    if main_services_df is None:
        return None
    
    print("\n" + "=" * 80)
    print("РАСЧЕТ СТОИМОСТИ ПО ПАЦИЕНТАМ")
    print("=" * 80)
    
    # Группируем по ЕНП
    patient_costs = []
    
    for enp in main_services_df['ЕНП'].unique():
        if pd.isna(enp):  # Пропускаем пустые ЕНП
            continue
            
        patient_data = main_services_df[main_services_df['ЕНП'] == enp]
        
        if len(patient_data) == 0:  # Пропускаем если нет данных
            continue
        
        # Получаем информацию о пациенте
        patient_info = patient_data.iloc[0]
        
        # Определяем этапы
        dr1_data = patient_data[patient_data['Тип талона'] == 'ДР1']
        dr2_data = patient_data[patient_data['Тип талона'] == 'ДР2']
        
        # Стоимости по этапам
        dr1_cost = dr1_data['Стоимость'].sum() if len(dr1_data) > 0 else 0
        dr2_cost = dr2_data['Стоимость'].sum() if len(dr2_data) > 0 else 0
        
        # Проверяем направление на II этап
        stage2_directed = any('Направлен на II этап' in str(health_group) 
                            for health_group in patient_data['Группа здоровья'])
        
        # Группа здоровья из ДР1
        health_group_dr1 = dr1_data['Группа здоровья'].iloc[0] if len(dr1_data) > 0 else ''
        
        # Группа здоровья из ДР2 (итоговая, без "Направлен на II этап")
        health_group_dr2 = dr2_data['Группа здоровья'].iloc[0] if len(dr2_data) > 0 else ''
        
        # Доктора по этапам
        dr1_doctor = dr1_data['Доктор-Услуги (ФИО)'].iloc[0] if len(dr1_data) > 0 else ''
        dr2_doctor = dr2_data['Доктор-Услуги (ФИО)'].iloc[0] if len(dr2_data) > 0 else ''
        
        # Подразделения по этапам
        dr1_department = dr1_data['Подразделение врача-Услуги'].iloc[0] if len(dr1_data) > 0 else ''
        dr2_department = dr2_data['Подразделение врача-Услуги'].iloc[0] if len(dr2_data) > 0 else ''
        
        # Статусы по этапам
        dr1_status = dr1_data['Статус'].iloc[0] if len(dr1_data) > 0 else ''
        dr2_status = dr2_data['Статус'].iloc[0] if len(dr2_data) > 0 else ''
        
        # Номера талонов по этапам
        dr1_talon = dr1_data['Номер талона'].iloc[0] if len(dr1_data) > 0 else ''
        dr2_talon = dr2_data['Номер талона'].iloc[0] if len(dr2_data) > 0 else ''
        
        # Маршрут из ДР1
        dr1_route = dr1_data['Маршрут'].iloc[0] if len(dr1_data) > 0 else ''
        
        patient_costs.append({
            'ЕНП': str(int(enp)) if not pd.isna(enp) else '',  # Сохраняем как строку без .0
            'Номер полиса': str(int(patient_info['Номер полиса'])) if not pd.isna(patient_info['Номер полиса']) else '',  # Сохраняем как строку без .0
            'Фамилия': patient_info['Фамилия'],
            'Имя': patient_info['Имя'],
            'Отчество': patient_info['Отчество'],
            'Пол': patient_info['Пол'],
            'Дата рождения': patient_info['Дата рождения'],
            'Маршрут ДР1': dr1_route,
            'Группа здоровья ДР1': health_group_dr1,
            'Группа здоровья ДР2': health_group_dr2,
            'Направлен на II этап': stage2_directed,
            'Стоимость ДР1': dr1_cost,
            'Стоимость ДР2': dr2_cost,
            'Общая стоимость': dr1_cost + dr2_cost,
            'Количество талонов ДР1': len(dr1_data),
            'Статус ДР1': dr1_status,
            'Количество талонов ДР2': len(dr2_data),
            'Статус ДР2': dr2_status,
            'Номер талона ДР1': dr1_talon,
            'Номер талона ДР2': dr2_talon,
            'Доктор ДР1': dr1_doctor,
            'Доктор ДР2': dr2_doctor,
            'Подразделение ДР1': dr1_department,
            'Подразделение ДР2': dr2_department
        })
    
    patient_costs_df = pd.DataFrame(patient_costs)
    
    print(f"Обработано пациентов: {len(patient_costs_df)}")
    print(f"Стоимость по этапам:")
    print(f"  ДР1: {patient_costs_df['Стоимость ДР1'].sum():.2f} руб.")
    print(f"  ДР2: {patient_costs_df['Стоимость ДР2'].sum():.2f} руб.")
    print(f"  Общая: {patient_costs_df['Общая стоимость'].sum():.2f} руб.")
    
    return patient_costs_df

def analyze_costs_by_demographics(patient_costs_df):
    """Анализ стоимости по демографическим группам"""
    
    if patient_costs_df is None:
        return
    
    print("\n" + "=" * 80)
    print("АНАЛИЗ СТОИМОСТИ ПО ДЕМОГРАФИЧЕСКИМ ГРУППАМ")
    print("=" * 80)
    
    # Анализ по полу
    print("\n1. АНАЛИЗ ПО ПОЛУ:")
    print("-" * 40)
    by_gender = patient_costs_df.groupby('Пол').agg({
        'Общая стоимость': ['sum', 'mean', 'count'],
        'Стоимость ДР1': 'sum',
        'Стоимость ДР2': 'sum'
    }).round(2)
    print(by_gender)
    
    # Анализ по направлению на II этап
    print("\n2. АНАЛИЗ ПО НАПРАВЛЕНИЮ НА II ЭТАП:")
    print("-" * 40)
    by_stage2 = patient_costs_df.groupby('Направлен на II этап').agg({
        'Общая стоимость': ['sum', 'mean', 'count'],
        'Стоимость ДР1': 'sum',
        'Стоимость ДР2': 'sum'
    }).round(2)
    print(by_stage2)
    
    # Анализ по группам здоровья
    print("\n3. АНАЛИЗ ПО ГРУППАМ ЗДОРОВЬЯ ДР1:")
    print("-" * 40)
    health_groups_dr1 = patient_costs_df['Группа здоровья ДР1'].value_counts()
    print(health_groups_dr1)
    
    print("\n4. АНАЛИЗ ПО ГРУППАМ ЗДОРОВЬЯ ДР2:")
    print("-" * 40)
    health_groups_dr2 = patient_costs_df['Группа здоровья ДР2'].value_counts()
    print(health_groups_dr2)
    
    # Топ-10 самых дорогих пациентов
    print("\n5. ТОП-10 САМЫХ ДОРОГИХ ПАЦИЕНТОВ:")
    print("-" * 40)
    top_patients = patient_costs_df.nlargest(10, 'Общая стоимость')
    print(top_patients[['Фамилия', 'Имя', 'Отчество', 'Пол', 'Общая стоимость', 'Стоимость ДР1', 'Стоимость ДР2']].to_string(index=False))

def save_results(patient_costs_df):
    """Сохранение результатов анализа"""
    
    print("\n" + "=" * 80)
    print("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    print("=" * 80)
    
    # Excel файл с одним листом
    excel_file = "dr_analysis_results.xlsx"
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Сохраняем лист с пациентами
        patient_costs_df.to_excel(writer, sheet_name='Стоимость по пациентам', index=False)
        
        # Получаем лист для форматирования
        worksheet = writer.sheets['Стоимость по пациентам']
        
        # Устанавливаем формат текста для колонок ЕНП и Номер полиса
        from openpyxl.styles import NamedStyle
        
        # Создаем стиль для текста
        text_style = NamedStyle(name="text_style")
        text_style.number_format = '@'  # Текстовый формат
        
        # Применяем текстовый формат к колонкам ЕНП (A) и Номер полиса (B)
        for row in range(2, len(patient_costs_df) + 2):  # Начинаем с 2, так как 1 - заголовок
            worksheet[f'A{row}'].number_format = '@'  # ЕНП
            worksheet[f'B{row}'].number_format = '@'  # Номер полиса
    
    print(f"Результаты сохранены:")
    print(f"  Excel: {excel_file}")

def main():
    """Основная функция"""
    
    print("АНАЛИЗ ДАННЫХ ДИСПАНСЕРИЗАЦИИ ДР1 И ДР2")
    print("=" * 80)
    
    # Загружаем данные
    combined_df, dr1_df, dr2_df = load_dr_data()
    
    if combined_df is None:
        return
    
    # Фильтруем по B кодам
    b_codes_df = filter_b_codes(combined_df)
    
    # Определяем основные услуги
    main_services_df = identify_main_services(b_codes_df)
    
    # Рассчитываем стоимость по пациентам
    patient_costs_df = calculate_patient_costs(main_services_df)
    
    # Сохраняем результаты
    save_results(patient_costs_df)
    
    print("\n" + "=" * 80)
    print("АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 80)

if __name__ == "__main__":
    main()
