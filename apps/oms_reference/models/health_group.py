from django.db import models
from datetime import datetime

health_group_data = {
    1: {"drname": "Присвоена I группа здоровья", "datebeg": "2013-12-26", "dateend": None},
    2: {"drname": "Присвоена II группа здоровья", "datebeg": "2013-12-26", "dateend": None},
    3: {"drname": "Присвоена III группа здоровья", "datebeg": "2013-12-26", "dateend": None},
    4: {"drname": "Присвоена IV группа здоровья", "datebeg": "2013-12-26", "dateend": None},
    5: {"drname": "Присвоена V группа здоровья", "datebeg": "2013-12-26", "dateend": None},
    6: {"drname": "Направлен на II этап диспансеризации", "datebeg": "2013-12-26", "dateend": "2014-03-06"},
    7: {"drname": "Проведен периодический медицинский осмотр несовершеннолетнему", "datebeg": "2013-12-26",
        "dateend": "2017-12-31"},
    11: {"drname": "Направлен на II этап диспансеризации, предварительно присвоена I группа здоровья",
         "datebeg": "2014-03-06", "dateend": "2018-03-31"},
    12: {"drname": "Направлен на II этап диспансеризации, предварительно присвоена II группа здоровья",
         "datebeg": "2014-03-06", "dateend": "2018-03-31"},
    13: {"drname": "Направлен на II этап диспансеризации, предварительно присвоена III группа здоровья",
         "datebeg": "2014-03-06", "dateend": "2015-12-31"},
    14: {"drname": "Направлен на II этап диспансеризации, предварительно присвоена IIIа группа здоровья",
         "datebeg": "2015-04-01", "dateend": "2018-03-31"},
    15: {"drname": "Направлен на II этап диспансеризации, предварительно присвоена IIIб группа здоровья",
         "datebeg": "2015-04-01", "dateend": "2018-03-31"},
    16: {
        "drname": "Проведен I этап диспансеризации определенных групп взрослого населения с периодичностью 1 раз в 2 года",
        "datebeg": "2018-01-01", "dateend": "2019-05-31"},
    17: {
        "drname": "Направлен на II этап диспансеризации или профилактического медицинского осмотра несовершеннолетних, предварительно присвоена IV группа здоровья",
        "datebeg": "2018-04-01", "dateend": None},
    18: {
        "drname": "Направлен на II этап диспансеризации или профилактического медицинского осмотра несовершеннолетних, предварительно присвоена V группа здоровья",
        "datebeg": "2018-04-01", "dateend": None},
    19: {
        "drname": "Направлен на II этап диспансеризации или профилактического медицинского осмотра несовершеннолетних, предварительно присвоена III группа здоровья",
        "datebeg": "2018-04-01", "dateend": None},
    31: {"drname": "Присвоена IIIа группа здоровья", "datebeg": "2015-04-01", "dateend": None},
    32: {"drname": "Присвоена IIIб группа здоровья", "datebeg": "2015-04-01", "dateend": None},
    33: {
        "drname": "Направлен на II этап диспансеризации определенных групп взрослого населения и углубленной диспансеризации, предварительно присвоена IIIа группа здоровья",
        "datebeg": "2021-07-01", "dateend": None},
    34: {
        "drname": "Направлен на II этап диспансеризации определенных групп взрослого населения и углубленной диспансеризации, предварительно присвоена IIIб группа здоровья",
        "datebeg": "2021-07-01", "dateend": None},
    35: {"drname": "Присвоена I группа репродуктивного здоровья", "datebeg": "2024-01-01", "dateend": None},
    36: {"drname": "Присвоена II группа репродуктивного здоровья", "datebeg": "2024-01-01", "dateend": None},
    37: {"drname": "Присвоена III группа репродуктивного здоровья", "datebeg": "2024-01-01", "dateend": None},
    38: {"drname": "Направлен на II этап диспансеризации, предварительно присвоена II группа репродуктивного здоровья",
         "datebeg": "2024-01-01", "dateend": None},
    39: {"drname": "Направлен на II этап диспансеризации, предварительно присвоена III группа репродуктивного здоровья",
         "datebeg": "2024-01-01", "dateend": None},
}


class HealthGroup(models.Model):
    """
    Модель группы здоровья при диспансеризации
    """

    iddr = models.PositiveIntegerField(primary_key=True, verbose_name="ID группы")
    drname = models.CharField(max_length=255, verbose_name="Название группы")
    datebeg = models.DateField(verbose_name="Дата начала", null=True, blank=True)
    dateend = models.DateField(verbose_name="Дата окончания", null=True, blank=True)

    class Meta:
        verbose_name = "Группа здоровья"
        verbose_name_plural = "Группы здоровья"

    def __str__(self):
        return f"{self.drname} ({self.datebeg} - {self.dateend if self.dateend else 'настоящее время'})"

    @staticmethod
    def populate_from_dict(data):
        """
        Метод для синхронизации таблицы с данными из словаря
        """
        # Получить все существующие данные
        existing_records = {
            record.iddr: {
                "drname": record.drname,
                "datebeg": record.datebeg.isoformat() if record.datebeg else None,
                "dateend": record.dateend.isoformat() if record.dateend else None,
            }
            for record in HealthGroup.objects.all()
        }

        # Проверить, отличаются ли данные
        if existing_records == data:
            return

        # Если данные отличаются, удалить старые и записать новые
        HealthGroup.objects.all().delete()
        for iddr, details in data.items():
            datebeg = (
                datetime.strptime(details["datebeg"], "%Y-%m-%d").date()
                if details["datebeg"]
                else None
            )
            dateend = (
                datetime.strptime(details["dateend"], "%Y-%m-%d").date()
                if details["dateend"]
                else None
            )
            HealthGroup.objects.create(
                iddr=iddr,
                drname=details["drname"],
                datebeg=datebeg,
                dateend=dateend,
            )
        print("Таблица HealthGroup синхронизирована с словарем!")
