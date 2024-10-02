from django.db import models


class GeneralOMSTarget(models.Model):
    code = models.CharField("Код цели", max_length=10)
    name = models.CharField("Наименование цели", max_length=255)
    start_date = models.DateField("Дата начала действия", blank=True, null=True)
    end_date = models.DateField("Дата окончания действия", blank=True, null=True)

    class Meta:
        verbose_name = "Общая цель ОМС"
        verbose_name_plural = "Общие цели ОМС"

    def __str__(self):
        return self.code


class MedicalOrganizationOMSTarget(models.Model):
    organization = models.ForeignKey(
        'organization.MedicalOrganization',
        on_delete=models.CASCADE,
        related_name='oms_targets',
        verbose_name="Медицинская организация"
    )
    general_target = models.ForeignKey(
        GeneralOMSTarget,
        on_delete=models.CASCADE,
        related_name='organization_targets',
        verbose_name="Общая цель ОМС"
    )
    is_active = models.BooleanField("Цель активна", default=True)
    start_date = models.DateField("Дата начала действия", blank=True, null=True)
    end_date = models.DateField("Дата окончания действия", blank=True, null=True)

    class Meta:
        verbose_name = "Цель ОМС медицинской организации"
        verbose_name_plural = "Цели ОМС медицинской организации"
        unique_together = ('organization', 'general_target')

    def __str__(self):
        return f"{self.organization.name} - {self.general_target.name}"
