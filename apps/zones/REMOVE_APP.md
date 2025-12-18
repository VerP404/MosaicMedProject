# Инструкция по полному удалению приложения zones

## ✅ Что уже сделано

1. ✅ Удалено `'apps.zones'` из `INSTALLED_APPS` в:
   - `config/settings/base.py`
   - `mosaic/config/settings.py`

## 📋 Что нужно проверить вручную

### 1. Проверка миграций в базе данных

Выполните SQL запрос в PostgreSQL:

```sql
-- Проверяем, есть ли миграции zones в базе
SELECT * FROM django_migrations WHERE app = 'zones';

-- Если есть записи, удалите их:
DELETE FROM django_migrations WHERE app = 'zones';
```

### 2. Проверка таблиц в базе данных

Проверьте, есть ли таблицы приложения zones:

```sql
-- Список всех таблиц zones
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name LIKE 'zones_%';

-- Если есть таблицы, удалите их (ОСТОРОЖНО!):
-- DROP TABLE IF EXISTS zones_siteaddress CASCADE;
-- DROP TABLE IF EXISTS zones_site CASCADE;
-- DROP TABLE IF EXISTS zones_corpusaddress CASCADE;
-- DROP TABLE IF EXISTS zones_corpus CASCADE;
-- DROP TABLE IF EXISTS zones_organization CASCADE;
-- DROP TABLE IF EXISTS zones_sitetype CASCADE;
-- DROP TABLE IF EXISTS zones_address CASCADE;
```

### 3. Удаление папки приложения (опционально)

Если хотите полностью удалить приложение:

```powershell
# Удалить всю папку apps/zones
Remove-Item -Recurse -Force "C:\DjangoProject\MosaicMedProject\apps\zones"
```

**Внимание:** Это удалит все файлы приложения, включая модели, админку и данные в папке `data/`.

### 4. Проверка ссылок в других файлах

Убедитесь, что нет импортов или ссылок на zones:

```powershell
# Поиск всех упоминаний zones в проекте
Get-ChildItem -Recurse -Include *.py | Select-String -Pattern "zones|Zones" | Select-Object Path, LineNumber, Line
```

## 🔍 Проверка после удаления

После выполнения всех шагов проверьте:

```bash
python manage.py check
python manage.py showmigrations
```

Не должно быть ошибок, связанных с zones.

## ⚠️ Важно

- Если в базе данных уже есть данные из приложения zones, их нужно будет удалить вручную через SQL
- Если другие приложения ссылаются на zones (ForeignKey, ManyToMany), нужно сначала удалить эти связи
- Рекомендуется сделать резервную копию базы данных перед удалением таблиц


