# Модуль ДН (как ИСЗЛ, но лучше)

## Пайплайн

1. **Bronze ИСЗЛ** — `load_data_dispansery_iszl` (все годы, upsert по `pdwid`).
2. **Справочник 168н** — `dn_reference` (`import_dn_diagnoses_168n`).
3. **Silver** — `sync_dn_from_iszl` → Person / DnLine / DnFact.
4. **Bronze Квазар** — `load_dn_kvazar` → `load_data_dn_kvazar`.
5. **UI** `/head/dn`.

```bash
python manage.py load_iszl_dn_years --clear
python manage.py import_dn_diagnoses_168n
python manage.py sync_dn_from_iszl --year=2026
python manage.py load_dn_kvazar --clear
```

## Логика ключей

- **ldwID** — запись диагноза у пациента (линии ДН).
- **pdwID** — строка плана на год/месяц.
- В отчётах за год на один ldwID берётся **последний месяц** плана.

## UI

- Карточка пациента: диагнозы, группа 168н, ИСЗЛ/Квазар, талоны года, незакрытые.
- Сводка ИСЗЛ, не прошедшие, вне 168н→305.
- «Нет в текущем / снять·внести» — нет в выбранном году / диагнозы к снятию или внесению.
- Квазар ↔ ИСЗЛ — обе стороны + % схожести, группа и участок.
- Excel: текущая вкладка / всё / карточка.
