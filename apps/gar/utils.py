"""
Утилиты для работы с данными ГАР
"""
import re
from typing import Dict, Optional


def parse_gar_address(row: Dict, table_name: str) -> Optional[Dict]:
    """
    Парсит строку данных ГАР и возвращает словарь для создания GarAddress
    
    Основные таблицы ГАР:
    - ADDR_OBJ - адресные объекты (регионы, районы, города, улицы)
    - HOUSES - дома
    - APARTMENTS - квартиры
    """
    result = {
        'gar_object_id': None,
        'parent_id': None,
        'region_code': None,
        'area': None,
        'city': None,
        'settlement': None,
        'street': None,
        'house': None,
        'apartment': None,
        'postal_code': None,
        'full_address': None,
        'object_level': None,
        'is_active': True,
    }

    # Получаем ID объекта
    object_id_fields = ['OBJECTID', 'OBJECT_ID', 'ID', 'GAR_ID']
    for field in object_id_fields:
        if field in row and row[field]:
            try:
                result['gar_object_id'] = int(row[field])
                break
            except (ValueError, TypeError):
                continue

    # Получаем родительский ID
    parent_id_fields = ['PARENTOBJID', 'PARENT_OBJ_ID', 'PARENT_ID']
    for field in parent_id_fields:
        if field in row and row[field]:
            try:
                result['parent_id'] = int(row[field]) if row[field] else None
                break
            except (ValueError, TypeError):
                continue

    # Получаем уровень объекта
    level_fields = ['LEVEL', 'OBJECT_LEVEL', 'LEVELID']
    for field in level_fields:
        if field in row and row[field]:
            try:
                result['object_level'] = int(row[field])
                break
            except (ValueError, TypeError):
                continue

    # Получаем код региона (первые 2 символа кода)
    region_fields = ['REGIONCODE', 'REGION_CODE', 'CODE']
    for field in region_fields:
        if field in row and row[field]:
            code = str(row[field]).strip()
            if len(code) >= 2:
                result['region_code'] = code[:2]
            break

    # Получаем название объекта
    name_fields = ['NAME', 'FORMALNAME', 'FORMAL_NAME', 'OFFNAME', 'OFF_NAME']
    name = None
    for field in name_fields:
        if field in row and row[field]:
            name = str(row[field]).strip()
            if name:
                break

    # Получаем тип объекта
    type_fields = ['SHORTNAME', 'SHORT_NAME', 'AOLEVEL', 'AO_LEVEL']
    obj_type = None
    for field in type_fields:
        if field in row and row[field]:
            obj_type = str(row[field]).strip()
            break

    # Определяем тип адресного объекта по уровню и типу
    if result['object_level']:
        level = result['object_level']
        
        # Уровни ГАР:
        # 1 - регион
        # 2 - район
        # 3 - город/село
        # 4 - улица
        # 5 - дом
        # 6 - квартира
        
        if level == 1:
            # Регион
            result['area'] = name
        elif level == 2:
            # Район
            result['area'] = name
        elif level == 3:
            # Город или населенный пункт
            if obj_type and obj_type.upper() in ['Г', 'ГОР', 'ГОРОД']:
                result['city'] = name
            else:
                result['settlement'] = name
        elif level == 4:
            # Улица
            result['street'] = name
        elif level == 5:
            # Дом
            result['house'] = name
        elif level == 6:
            # Квартира
            result['apartment'] = name

    # Альтернативный способ определения по типу объекта
    if not result['object_level'] and obj_type:
        obj_type_upper = obj_type.upper()
        if any(t in obj_type_upper for t in ['УЛ', 'УЛИЦА', 'ПЕР', 'ПЕРЕУЛОК', 'ПР', 'ПРОСПЕКТ']):
            result['street'] = name
        elif any(t in obj_type_upper for t in ['Г', 'ГОР', 'ГОРОД']):
            result['city'] = name
        elif any(t in obj_type_upper for t in ['Р', 'РАЙОН']):
            result['area'] = name
        elif any(t in obj_type_upper for t in ['Д', 'ДОМ']):
            result['house'] = name
        elif any(t in obj_type_upper for t in ['КВ', 'КВАРТИРА']):
            result['apartment'] = name

    # Получаем почтовый индекс
    postal_fields = ['POSTALCODE', 'POSTAL_CODE', 'INDEX', 'POSTCODE']
    for field in postal_fields:
        if field in row and row[field]:
            result['postal_code'] = str(row[field]).strip()
            break

    # Формируем полный адрес
    address_parts = []
    if result['area']:
        address_parts.append(result['area'])
    if result['city']:
        address_parts.append(result['city'])
    if result['settlement']:
        address_parts.append(result['settlement'])
    if result['street']:
        address_parts.append(result['street'])
    if result['house']:
        address_parts.append(f"д. {result['house']}")
    if result['apartment']:
        address_parts.append(f"кв. {result['apartment']}")

    result['full_address'] = ', '.join(address_parts) if address_parts else None

    # Проверяем, что есть хотя бы gar_object_id
    if not result['gar_object_id']:
        return None

    return result


def build_address_hierarchy(addresses: list) -> Dict:
    """
    Строит иерархию адресов на основе parent_id
    """
    address_dict = {addr.gar_object_id: addr for addr in addresses}
    hierarchy = {}

    for addr in addresses:
        if addr.parent_id and addr.parent_id in address_dict:
            parent = address_dict[addr.parent_id]
            if parent.gar_object_id not in hierarchy:
                hierarchy[parent.gar_object_id] = []
            hierarchy[parent.gar_object_id].append(addr.gar_object_id)

    return hierarchy



