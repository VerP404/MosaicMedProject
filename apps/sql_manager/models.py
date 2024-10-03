from django.db import models


class CategorySQLQuery(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class TypeSQLQuery(models.Model):
    name = models.CharField(max_length=100, verbose_name="Тип запроса")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип"
        verbose_name_plural = "Типы"


class SQLQuery(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    category = models.ForeignKey(CategorySQLQuery, on_delete=models.SET_DEFAULT, default=1, verbose_name="Категория")
    query_type = models.ForeignKey(TypeSQLQuery, on_delete=models.SET_DEFAULT, default=1, verbose_name="Тип")
    query = models.TextField(verbose_name="SQL Запрос")
    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Запрос"
        verbose_name_plural = "Запросы"
