import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.references.models import MKB10


class Command(BaseCommand):
    help = 'Загрузка данных МКБ-10 из XML файла'

    def add_arguments(self, parser):
        parser.add_argument('xml_file', type=str, help='Путь к XML файлу с данными МКБ-10')

    def handle(self, *args, **options):
        xml_file = options['xml_file']
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            with transaction.atomic():
                # Словарь для хранения существующих объектов
                existing_mkb = {mkb.code: mkb for mkb in MKB10.objects.all()}
                
                # Словарь для хранения новых/обновленных объектов
                mkb_dict = {}
                
                # Сначала создаем или обновляем все объекты без связей
                for mkb in root.findall('MKB10'):
                    code = mkb.find('id').text.strip()
                    name = mkb.find('Name').text.strip()
                    is_active = mkb.find('FlagOms').text == '1'
                    
                    # Определяем уровень по длине кода
                    level = 1 if len(code.split('.')) == 1 else 2
                    
                    if code in existing_mkb:
                        # Обновляем существующий объект
                        mkb_obj = existing_mkb[code]
                        mkb_obj.name = name
                        mkb_obj.level = level
                        mkb_obj.is_active = is_active
                        mkb_obj.save()
                    else:
                        # Создаем новый объект
                        mkb_obj = MKB10.objects.create(
                            code=code,
                            name=name,
                            level=level,
                            is_active=is_active
                        )
                    
                    mkb_dict[code] = mkb_obj
                
                # Теперь устанавливаем связи parent
                for code, mkb_obj in mkb_dict.items():
                    if '.' in code:
                        parent_code = code.split('.')[0]
                        if parent_code in mkb_dict:
                            mkb_obj.parent = mkb_dict[parent_code]
                            mkb_obj.save()
                
                # Деактивируем коды, которых нет в новом файле
                new_codes = set(mkb_dict.keys())
                for code, mkb in existing_mkb.items():
                    if code not in new_codes:
                        mkb.is_active = False
                        mkb.save()
                
                # Обновляем флаг is_final для всех записей
                for mkb in MKB10.objects.all():
                    mkb.save()  # Это вызовет пересчет is_final
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Успешно обновлено {len(mkb_dict)} записей МКБ-10\n'
                        f'Обновлено: {len([m for m in mkb_dict.values() if m.code in existing_mkb])}\n'
                        f'Создано: {len([m for m in mkb_dict.values() if m.code not in existing_mkb])}\n'
                        f'Деактивировано: {len([m for m in existing_mkb.values() if m.code not in new_codes])}\n'
                        f'Конечных диагнозов: {MKB10.objects.filter(is_final=True).count()}'
                    )
                )
                
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Файл {xml_file} не найден')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при загрузке данных: {str(e)}')
            ) 