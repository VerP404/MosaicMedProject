# Документация

---
# Экспорт и импорт данных для общих таблиц
Обновление данных автоматически происходит через выполнение скрипта [update_MosaicMed.sh](scripts%2Fupdate_MosaicMed.sh) 
### Расположение файлов команд экспорта и импорта

- **Путь к команде экспорта**: [data_export.py](apps%2Fdata_loader%2Fmanagement%2Fcommands%2Fdata_export.py)`apps/data_loader/management/commands/data_export.py`
- **Путь к команде импорта**: [data_import.py](apps%2Fdata_loader%2Fmanagement%2Fcommands%2Fdata_import.py)`apps/data_loader/management/commands/data_import.py`

### Запуск команд экспорта и импорта

- **Команда экспорта**: Чтобы выполнить экспорт данных, выполните следующую команду:

``` bash
python manage.py data_export
```

- **Команда импорта**: Чтобы выполнить импорт данных, выполните следующую команду:

``` bash
python manage.py data_import
```
