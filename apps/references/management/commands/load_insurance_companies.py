import xml.etree.ElementTree as ET
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from references.models import InsuranceCompany


class Command(BaseCommand):
    help = 'Загрузка данных страховых медицинских организаций из XML файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к XML файлу')

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Получаем версию и дату файла
            version = root.find('version').text
            file_date = datetime.strptime(root.find('date').text, '%d.%m.%Y').date()
            
            self.stdout.write(f'Загрузка данных СМО из файла версии {version} от {file_date}')
            
            # Сохраняем существующие записи
            existing_companies = {
                company.smocod: company
                for company in InsuranceCompany.objects.all()
            }
            
            # Счетчики для статистики
            stats = {
                'created': 0,
                'updated': 0,
                'deactivated': 0,
                'total': 0
            }
            
            with transaction.atomic():
                # Обрабатываем каждую СМО
                for company_elem in root.findall('.//insCompany'):
                    stats['total'] += 1
                    
                    # Получаем данные из XML
                    smocod = company_elem.find('smocod').text
                    
                    # Подготовка данных
                    data = {
                        'tf_okato': company_elem.find('tf_okato').text,
                        'smocod': smocod,
                        'nam_smop': company_elem.find('nam_smop').text,
                        'nam_smok': company_elem.find('nam_smok').text,
                        'inn': company_elem.find('inn').text,
                        'ogrn': company_elem.find('Ogrn').text,
                        'kpp': company_elem.find('KPP').text,
                        
                        # Юридический адрес
                        'jur_address_index': company_elem.find('.//jurAddress/index_j').text,
                        'jur_address': company_elem.find('.//jurAddress/addr_j').text,
                        
                        # Почтовый адрес
                        'pst_address_index': company_elem.find('.//pstAddress/index_f').text,
                        'pst_address': company_elem.find('.//pstAddress/addr_f').text,
                        
                        'okopf': company_elem.find('okopf').text,
                        
                        # Руководитель
                        'head_lastname': company_elem.find('fam_ruk').text,
                        'head_firstname': company_elem.find('im_ruk').text,
                        'head_middlename': company_elem.find('ot_ruk').text,
                        
                        # Контакты
                        'phone': company_elem.find('phone').text,
                        'fax': company_elem.find('fax').text,
                        'hot_line': company_elem.find('hot_line').text,
                        'email': company_elem.find('e_mail').text,
                        'website': company_elem.find('www').text or None,
                        
                        # Лицензия
                        'license_number': company_elem.find('.//licenziy/n_doc').text,
                        'license_start_date': datetime.strptime(
                            company_elem.find('.//licenziy/d_start').text,
                            '%d.%m.%Y'
                        ).date(),
                        'license_end_date': datetime.strptime(
                            company_elem.find('.//licenziy/date_e').text,
                            '%d.%m.%Y'
                        ).date(),
                        
                        'org_type': company_elem.find('org').text,
                        
                        # Статистика
                        'year_work': int(company_elem.find('.//insAdvice/YEAR_WORK').text),
                        'last_update': datetime.strptime(
                            company_elem.find('.//insAdvice/DUVED').text,
                            '%d.%m.%Y'
                        ).date(),
                        'insured_count': int(company_elem.find('.//insAdvice/kol_zl').text),
                    }
                    
                    # Обновляем или создаем запись
                    if smocod in existing_companies:
                        company = existing_companies[smocod]
                        for key, value in data.items():
                            setattr(company, key, value)
                        company.is_active = True
                        company.save()
                        stats['updated'] += 1
                    else:
                        company = InsuranceCompany.objects.create(**data)
                        stats['created'] += 1
                    
                    # Удаляем из словаря существующих
                    existing_companies.pop(smocod, None)
                
                # Деактивируем оставшиеся записи
                for company in existing_companies.values():
                    company.is_active = False
                    company.save()
                    stats['deactivated'] += 1
            
            # Выводим статистику
            self.stdout.write(self.style.SUCCESS(
                f'Загрузка завершена:\n'
                f'- Всего записей в файле: {stats["total"]}\n'
                f'- Создано новых: {stats["created"]}\n'
                f'- Обновлено: {stats["updated"]}\n'
                f'- Деактивировано: {stats["deactivated"]}'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при загрузке данных: {str(e)}')) 