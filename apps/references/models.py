from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone

# Create your models here.

class MKB10(models.Model):
    code = models.CharField(
        "Код МКБ-10",
        max_length=16,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]\d{2}(\.\d{1,2})?$',
                message='Код должен соответствовать формату МКБ-10 (например: A01.1)'
            )
        ]
    )
    name = models.CharField("Наименование", max_length=512)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children', verbose_name="Родительский код")
    level = models.PositiveIntegerField("Уровень иерархии", default=1)
    is_active = models.BooleanField("Активен", default=True)
    is_final = models.BooleanField("Конечный диагноз", default=False)
    description = models.TextField("Описание/Примечание", blank=True, null=True)
    created_at = models.DateTimeField("Дата создания", default=timezone.now)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "МКБ-10: диагноз"
        verbose_name_plural = "МКБ-10: диагнозы"
        ordering = ["code"]
        unique_together = ("code", "parent")
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"

    def get_full_path(self):
        """Возвращает полный путь диагноза в иерархии"""
        path = [self.code]
        current = self.parent
        while current:
            path.append(current.code)
            current = current.parent
        return ' / '.join(reversed(path))

    def get_children_count(self):
        """Возвращает количество дочерних элементов"""
        return self.children.count()

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
        self.is_final = not self.children.exists()
        super().save(*args, **kwargs)
