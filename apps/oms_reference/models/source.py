from django.db import models

source_data = {
    1: {'source_name': 'Web-ОМС'},
    2: {'source_name': 'Квазар 4'},
    3: {'source_name': 'МИС КАУЗ'},
}


class Source(models.Model):
    """
    Модель источника данных
    """
    id_source = models.PositiveIntegerField(primary_key=True, verbose_name="ID источника")
    source_name = models.CharField(max_length=255, verbose_name="Источник")

    class Meta:
        verbose_name = "Источник данных"
        verbose_name_plural = "Источники данных"

    def __str__(self):
        return f"{self.id_source} - {self.source_name}"

    @staticmethod
    def populate_from_dict(data):
        """
        Метод для синхронизации таблицы с данными из словаря
        """
        # Получить все существующие данные
        existing_records = {
            record.id_source: {
                "source_name": record.source_name,
            }
            for record in Source.objects.all()
        }

        # Проверить, отличаются ли данные
        if existing_records == data:
            return

        # Если данные отличаются, удалить старые и записать новые
        Source.objects.all().delete()
        for id_source, details in data.items():
            Source.objects.create(
                id_source=id_source,
                source_name=details["source_name"],
            )
        print("Таблица Source синхронизирована с словарем!")

