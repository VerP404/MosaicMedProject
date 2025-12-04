"""
Сервис для обработки CSV файлов диспансерного наблюдения
"""
import pandas as pd
import os
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from datetime import datetime

from ..models import Person, Encounter, Observation, DataImport


class DNCSVProcessor:
    """Обработчик CSV файлов для диспансерного наблюдения"""
    
    # Ожидаемые колонки в CSV
    REQUIRED_COLUMNS = ['ENP', 'FIO', 'DR', 'DS']
    OPTIONAL_COLUMNS = ['PlanYear', 'PlanMonth', 'PID', 'LDWID', 'PDWID', 'DateBegin', 'DateEnd']
    
    def __init__(self, file_path, year):
        self.file_path = file_path
        self.year = year
        self.import_batch = None
        self.stats = {
            'total_rows': 0,
            'processed_rows': 0,
            'created_persons': 0,
            'updated_persons': 0,
            'created_encounters': 0,
            'created_observations': 0,
            'errors': []
        }
    
    def process(self):
        """Основной метод обработки CSV файла"""
        try:
            # Создаем запись о загрузке
            self.import_batch = DataImport.objects.create(
                year=self.year,
                file_name=os.path.basename(self.file_path),
                file_path=self.file_path,
                status='processing'
            )
            
            # Читаем CSV файл
            df = self._read_csv()
            if df is None or df.empty:
                raise ValueError("CSV файл пуст или не может быть прочитан")
            
            self.stats['total_rows'] = len(df)
            self.import_batch.total_rows = len(df)
            self.import_batch.save()
            
            # Обрабатываем данные
            with transaction.atomic():
                self._process_dataframe(df)
                
                # Определяем открепленных пациентов
                self._mark_detached_patients()
                
                # Сопоставляем с талонами ОМС
                self._match_with_oms_talons()
            
            # Обновляем статистику
            self.import_batch.processed_rows = self.stats['processed_rows']
            self.import_batch.created_persons = self.stats['created_persons']
            self.import_batch.updated_persons = self.stats['updated_persons']
            self.import_batch.created_encounters = self.stats['created_encounters']
            self.import_batch.created_observations = self.stats['created_observations']
            self.import_batch.detached_patients = self.stats.get('detached_count', 0)
            self.import_batch.status = 'completed'
            self.import_batch.save()
            
            return True, "Обработка завершена успешно"
            
        except Exception as e:
            if self.import_batch:
                self.import_batch.status = 'error'
                self.import_batch.error_message = str(e)
                self.import_batch.save()
            return False, f"Ошибка обработки: {str(e)}"
    
    def _read_csv(self):
        """Читает CSV файл с обработкой различных кодировок"""
        encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin1']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(
                    self.file_path,
                    sep=';',
                    encoding=encoding,
                    low_memory=False,
                    dtype=str
                )
                # Очищаем пробелы в названиях колонок
                df.columns = df.columns.str.strip()
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                raise ValueError(f"Ошибка чтения файла: {str(e)}")
        
        raise ValueError("Не удалось прочитать файл ни с одной из кодировок")
    
    def _process_dataframe(self, df):
        """Обрабатывает DataFrame и создает/обновляет записи"""
        # Проверяем наличие обязательных колонок
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}")
        
        # Очищаем ENP от лишних символов
        if 'ENP' in df.columns:
            df['ENP'] = df['ENP'].astype(str).str.replace('`', '').str.strip()
        
        # Группируем по ENP для обработки пациентов
        for enp, group in df.groupby('ENP'):
            if pd.isna(enp) or str(enp).strip() == '' or str(enp) == 'nan':
                continue
            
            try:
                self._process_patient_group(enp, group)
                self.stats['processed_rows'] += len(group)
            except Exception as e:
                self.stats['errors'].append(f"Ошибка обработки ENP {enp}: {str(e)}")
    
    def _process_patient_group(self, enp, group):
        """Обрабатывает группу записей для одного пациента"""
        # Берем первую запись для получения базовых данных пациента
        first_row = group.iloc[0]
        
        # Получаем или создаем пациента
        person, created = Person.objects.get_or_create(
            enp=str(enp).strip(),
            defaults={
                'fio': str(first_row.get('FIO', '')).strip(),
                'dr': self._parse_date(first_row.get('DR', '')),
                'is_detached': False,
                'detached_date': None,
                'last_import_date': timezone.now()
            }
        )
        
        if created:
            self.stats['created_persons'] += 1
        else:
            # Обновляем данные пациента
            person.fio = str(first_row.get('FIO', '')).strip() or person.fio
            if first_row.get('DR'):
                dr = self._parse_date(first_row.get('DR', ''))
                if dr:
                    person.dr = dr
            # Если пациент был откреплен, но снова появился - снимаем флаг
            if person.is_detached:
                person.is_detached = False
                person.detached_date = None
            person.last_import_date = timezone.now()
            person.save()
            self.stats['updated_persons'] += 1
        
        # Обрабатываем встречи (Encounter) и наблюдения (Observation)
        for _, row in group.iterrows():
            self._process_encounter_and_observation(person, row)
    
    def _process_encounter_and_observation(self, person, row):
        """Обрабатывает одну запись - создает Encounter и Observation"""
        # Получаем данные
        pid = str(row.get('PID', '')).strip() if pd.notna(row.get('PID')) else ''
        ldwid = str(row.get('LDWID', '')).strip() if pd.notna(row.get('LDWID')) else ''
        ds = str(row.get('DS', '')).strip() if pd.notna(row.get('DS')) else ''
        pdwid = str(row.get('PDWID', '')).strip() if pd.notna(row.get('PDWID')) else ''
        
        if not ldwid or not ds:
            return  # Пропускаем записи без обязательных данных
        
        # Получаем или создаем Encounter
        encounter, _ = Encounter.objects.get_or_create(
            person=person,
            ldwid=ldwid,
            ds=ds,
            defaults={'pid': pid}
        )
        
        if _:
            self.stats['created_encounters'] += 1
        
        # Получаем данные для Observation
        plan_year = self.year
        if pd.notna(row.get('PlanYear')):
            try:
                plan_year = int(float(str(row.get('PlanYear')).strip()))
            except (ValueError, TypeError):
                plan_year = self.year
        
        plan_month = str(row.get('PlanMonth', '')).strip() if pd.notna(row.get('PlanMonth')) else None
        date_begin = self._parse_date(row.get('DateBegin', '')) if pd.notna(row.get('DateBegin')) else None
        date_end = self._parse_date(row.get('DateEnd', '')) if pd.notna(row.get('DateEnd')) else None
        
        # Закрываем старые наблюдения для этого encounter и pdwid
        Observation.objects.filter(
            encounter=encounter,
            pdwid=pdwid,
            plan_year=plan_year,
            is_current=True
        ).update(
            is_current=False,
            effective_to=timezone.now()
        )
        
        # Создаем новое наблюдение
        observation = Observation.objects.create(
            encounter=encounter,
            pdwid=pdwid,
            plan_year=plan_year,
            plan_month=plan_month,
            date_begin=date_begin,
            date_end=date_end,
            status='planned',
            import_batch=self.import_batch,
            is_current=True
        )
        
        self.stats['created_observations'] += 1
    
    def _parse_date(self, date_str):
        """Парсит дату из строки в различных форматах"""
        if pd.isna(date_str) or not str(date_str).strip():
            return None
        
        date_str = str(date_str).strip()
        
        # Пробуем различные форматы
        formats = [
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%Y.%m.%d',
            '%d-%m-%Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _mark_detached_patients(self):
        """Помечает пациентов как открепленных, если их нет в текущей загрузке"""
        # Получаем ENP всех пациентов из текущей загрузки
        current_enps = set(
            Observation.objects.filter(
                import_batch=self.import_batch
            ).values_list('encounter__person__enp', flat=True).distinct()
        )
        
        # Находим пациентов, которые были в этом году в предыдущих загрузках, 
        # но отсутствуют в текущей загрузке
        previous_observations = Observation.objects.filter(
            plan_year=self.year,
            is_current=True
        ).exclude(
            import_batch=self.import_batch
        ).select_related('encounter__person')
        
        previous_enps = set(
            obs.encounter.person.enp for obs in previous_observations
        )
        
        # Пациенты, которые были раньше, но отсутствуют сейчас
        detached_enps = previous_enps - current_enps
        
        if detached_enps:
            # Помечаем пациентов как открепленных
            detached_count = Person.objects.filter(
                enp__in=detached_enps
            ).update(
                is_detached=True,
                detached_date=timezone.now()
            )
            
            # Также помечаем их наблюдения
            Observation.objects.filter(
                encounter__person__enp__in=detached_enps,
                plan_year=self.year,
                is_current=True
            ).exclude(
                import_batch=self.import_batch
            ).update(
                status='detached',
                is_current=False,
                effective_to=timezone.now()
            )
            
            self.stats['detached_count'] = detached_count
        else:
            self.stats['detached_count'] = 0
    
    def _match_with_oms_talons(self):
        """Сопоставляет наблюдения с талонами ОМС из load_data_oms_data"""
        from django.db import connection
        
        # Получаем все активные наблюдения за этот год
        observations = Observation.objects.filter(
            plan_year=self.year,
            is_current=True,
            status__in=['planned', 'not_completed']
        ).select_related('encounter__person')
        
        if not observations.exists():
            return
        
        # Получаем ENP пациентов
        enp_list = list(observations.values_list('encounter__person__enp', flat=True).distinct())
        
        if not enp_list:
            return
        
        # Формируем запрос к таблице load_data_oms_data
        enp_placeholders = ','.join([f"'{enp}'" for enp in enp_list])
        
        query = f"""
        SELECT 
            enp,
            talon,
            treatment_start,
            treatment_end,
            main_diagnosis_code,
            additional_diagnosis_codes,
            report_year
        FROM load_data_oms_data 
        WHERE enp IN ({enp_placeholders})
        AND report_year = {self.year}
        """
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                oms_records = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Сопоставляем наблюдения с талонами
            for observation in observations:
                person_enp = observation.encounter.person.enp
                diagnosis = observation.encounter.ds
                
                # Ищем соответствующие талоны
                matching_talons = [
                    talon for talon in oms_records
                    if talon['enp'] == person_enp and self._diagnosis_matches(
                        diagnosis, 
                        talon.get('main_diagnosis_code', ''),
                        talon.get('additional_diagnosis_codes', '')
                    )
                ]
                
                if matching_talons:
                    # Берем первый подходящий талон
                    talon = matching_talons[0]
                    observation.status = 'completed'
                    observation.talon_number = talon.get('talon', '')
                    
                    # Пытаемся определить дату посещения
                    if talon.get('treatment_end'):
                        try:
                            if isinstance(talon['treatment_end'], str):
                                observation.actual_date = self._parse_date(talon['treatment_end'])
                            else:
                                observation.actual_date = talon['treatment_end']
                        except:
                            pass
                    
                    observation.save()
                else:
                    # Если талонов нет, но наблюдение запланировано - помечаем как не выполненное
                    if observation.status == 'planned':
                        observation.status = 'not_completed'
                        observation.save()
        
        except Exception as e:
            # Логируем ошибку, но не прерываем процесс
            self.stats['errors'].append(f"Ошибка сопоставления с талонами ОМС: {str(e)}")
    
    def _diagnosis_matches(self, observation_diagnosis, main_diagnosis, additional_diagnoses):
        """Проверяет, соответствует ли диагноз наблюдения диагнозам в талоне"""
        if not observation_diagnosis:
            return False
        
        # Берем основной код диагноза (до пробела)
        obs_code = str(observation_diagnosis).split()[0] if ' ' in str(observation_diagnosis) else str(observation_diagnosis)
        obs_code = obs_code.strip().upper()
        
        # Проверяем основной диагноз
        if main_diagnosis:
            main_code = str(main_diagnosis).strip().upper()
            if obs_code == main_code or main_code.startswith(obs_code) or obs_code.startswith(main_code):
                return True
        
        # Проверяем сопутствующие диагнозы
        if additional_diagnoses and str(additional_diagnoses) != '-':
            additional_list = [d.strip().upper() for d in str(additional_diagnoses).split(',')]
            for add_code in additional_list:
                if obs_code == add_code or add_code.startswith(obs_code) or obs_code.startswith(add_code):
                    return True
        
        return False

