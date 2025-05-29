from django.db import models
from django.contrib.auth.models import User


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


class SavedQuery(models.Model):
    name = models.CharField("Название запроса", max_length=255)
    query = models.TextField("SQL запрос")
    description = models.TextField("Описание", blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Создал")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_public = models.BooleanField("Публичный запрос", default=False)

    class Meta:
        verbose_name = "Сохраненный запрос"
        verbose_name_plural = "Сохраненные запросы"
        ordering = ['-updated_at']

    def __str__(self):
        return self.name
