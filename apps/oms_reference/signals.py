from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models.goal import Goal, goal_data
from .models.health_group import HealthGroup, health_group_data
from .models.source import Source, source_data


@receiver(post_migrate)
def populate_health_group(sender, **kwargs):
    """
    Автоматическое заполнение таблицы HealthGroup
    """
    if sender.name == "apps.oms_reference":  # Проверяем, что сигнал запускается для текущего приложения
        HealthGroup.populate_from_dict(health_group_data)
        print("oms_reference.HealthGroup: данные проверены и обновлены.")


@receiver(post_migrate)
def populate_source(sender, **kwargs):
    """
    Автоматическое заполнение таблицы Source
    """
    if sender.name == "apps.oms_reference":
        Source.populate_from_dict(source_data)
        print("oms_reference.Source: данные проверены и обновлены.")


@receiver(post_migrate)
def populate_goal(sender, **kwargs):
    """
    Автоматическое заполнение таблицы Goal
    """
    if sender.name == "apps.oms_reference":
        Goal.populate_from_dict(goal_data)
        print("oms_reference.Goal: данные проверены и обновлены.")
