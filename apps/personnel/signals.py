import logging
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.urls import reverse
from apps.personnel.models import Person
from apps.home.models import TelegramGroup
from telegram import Bot
from telegram.request import HTTPXRequest
import asyncio

logger = logging.getLogger(__name__)


def run_async(coro):
    """Создает новый event loop для выполнения coroutine."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@receiver(m2m_changed, sender=Person.telegram_groups.through)
def sync_telegram_membership(sender, instance, action, reverse, pk_set, **kwargs):
    """
    При добавлении (post_add) отправляет сотруднику личное приглашение в группу.
    При удалении (post_remove) – уведомляет группу и исключает сотрудника из чата.

    В сообщениях вместо Telegram ID используются ФИО сотрудника (ссылка на админку)
    и название группы (также ссылка на админку группы).
    """
    if action not in ("post_add", "post_remove"):
        return

    if not instance.telegram:
        logger.warning("Сотрудник %s не имеет указанного Telegram ID", instance)
        return

    try:
        telegram_user_id = int(instance.telegram)
    except ValueError:
        logger.error("Неверный формат Telegram ID у %s: %s", instance, instance.telegram)
        return

    # Формируем ссылку на административную страницу сотрудника (пример)
    person_admin_url = f"/admin/personnel/person/{instance.pk}/change/"

    for group_pk in pk_set:
        try:
            group = TelegramGroup.objects.get(pk=group_pk)
            bot_entry = group.bot  # Объект TelegramBot, привязанный к группе
            req = HTTPXRequest(connect_timeout=20, read_timeout=20)
            bot = Bot(bot_entry.token, request=req)
            # Формируем ссылку на административную страницу группы (пример)
            group_admin_url = f"/admin/home/telegramgroup/{group.pk}/change/"

            if action == "post_add":
                async def addition_process():
                    # Получаем ссылку-приглашение для группы
                    invite_link = await bot.export_chat_invite_link(chat_id=group.group_id)
                    # Отправляем сообщение в группу о приглашении сотрудника с ФИО
                    await bot.send_message(
                        chat_id=group.group_id,
                        text=(
                            f"Сотруднику <a href='{person_admin_url}'>{instance}</a> "
                            f"отправлено личное приглашение в группу "
                            f"<a href='{group_admin_url}'>{group.name}</a>."
                        ),
                        parse_mode="HTML"
                    )
                    # Отправляем личное приглашение сотруднику
                    msg_text = (
                        f"Вас добавили в группу <a href='{group_admin_url}'>{group.name}</a>.\n"
                        f"Присоединяйтесь по ссылке: {invite_link}"
                    )
                    await bot.send_message(
                        chat_id=telegram_user_id,
                        text=msg_text,
                        parse_mode="HTML"
                    )

                run_async(addition_process())
                logger.info("Отправлено приглашение сотруднику %s для группы %s", instance, group.name)

            elif action == "post_remove":
                async def removal_process():
                    await bot.send_message(
                        chat_id=group.group_id,
                        text=(
                            f"Сотрудник <a href='{person_admin_url}'>{instance}</a> "
                            f"будет исключён из группы <a href='{group_admin_url}'>{group.name}</a>."
                        ),
                        parse_mode="HTML"
                    )
                    await bot.send_message(
                        chat_id=telegram_user_id,
                        text=(
                            f"Вы были исключены из группы <a href='{group_admin_url}'>{group.name}</a>."
                        ),
                        parse_mode="HTML"
                    )
                    await bot.ban_chat_member(chat_id=group.group_id, user_id=telegram_user_id)
                    await bot.unban_chat_member(chat_id=group.group_id, user_id=telegram_user_id)

                run_async(removal_process())
                logger.info("Исключён сотрудник %s из группы %s", instance, group.name)

        except Exception as e:
            logger.exception("Ошибка при обработке сотрудника %s для группы %s: %s", instance, group_pk, e)
