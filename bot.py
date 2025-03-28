import os
import sys
from pathlib import Path
import asyncio  # Импортируем asyncio для запуска event loop

from asgiref.sync import sync_to_async

# Определяем корневую директорию (если bot.py находится в корне проекта)
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
from telegram.request import HTTPXRequest  # Для работы с новой версией API
from apps.home.models import TelegramBot, TelegramGroup
from apps.personnel.models import Person
from apps.organization.models import MedicalOrganization  # для получения имени организации

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)


@sync_to_async
def get_bot_entry():
    return TelegramBot.objects.filter(alias="main_bot").first()


@sync_to_async
def get_person_by_telegram(telegram_id: str):
    return Person.objects.filter(telegram=telegram_id).first()


@sync_to_async
def get_first_org():
    return MedicalOrganization.objects.first()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Приветствие. Бот приветствует пользователя от имени медицинской организации, привязанной к боту.
    """
    user = update.effective_user
    org = await get_first_org()
    org_name = org.name if org else "Неизвестная организация"
    greeting = (
        f"Вас приветствует административный бот «{org_name}».\n"
        "Для просмотра Ваших групп используйте команду /mygroups\n"
        "Чтобы узнать свой Telegram ID, используйте команду /myid"
    )
    logger.info("Пользователь %s (%s) вызвал /start", user.id, user.first_name)
    await update.message.reply_text(greeting)


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Выводит Telegram ID пользователя.
    """
    user = update.effective_user
    await update.message.reply_text(
        f"Ваш Telegram ID: {user.id}. "
        f"\nДля привязки Вашего телеграм-аккаунта к Вашей учетной записи в системе, передайте id администратору")


async def mygroups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет пользователю список групп, в которых он состоит.
    Для каждой группы выводится название как гиперссылка.
    Для получения ссылки генерируется приглашение через Telegram API.
    """
    telegram_id = str(update.effective_user.id)
    try:
        person = await get_person_by_telegram(telegram_id)
        if not person:
            await update.message.reply_text("Ваш аккаунт не найден в базе. Обратитесь к администратору.")
            return
        groups = list(person.telegram_groups.all())
        if not groups:
            await update.message.reply_text("Вы не состоите ни в одной группе.")
            return

        response = "Вы состоите в следующих группах:\n"
        req = HTTPXRequest(connect_timeout=20, read_timeout=20)
        bot_entry = await get_bot_entry()
        if not bot_entry:
            await update.message.reply_text("Ошибка: не найден основной бот.")
            return
        bot = context.bot  # используем объект бота из контекста

        for group in groups:
            try:
                invite_link = await bot.export_chat_invite_link(chat_id=group.group_id)
            except Exception as e:
                logger.exception("Ошибка генерации приглашения для группы %s: %s", group.name, e)
                invite_link = "#"
            # Формируем гиперссылку: название группы → ссылка приглашения
            response += f"- <a href='{invite_link}'>{group.name}</a>\n"

        await update.message.reply_text(response, parse_mode="HTML")
    except Exception as e:
        logger.exception("Ошибка при получении ваших групп")
        await update.message.reply_text(f"Ошибка при получении групп: {e}")


def main():
    import asyncio
    # Создаем и устанавливаем новый event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Получаем объект бота через синхронную обёртку
    bot_entry = loop.run_until_complete(get_bot_entry())
    if not bot_entry:
        raise Exception("Бот с alias='main_bot' не найден.")
    token = bot_entry.token
    logger.info("Запуск бота с alias='main_bot'. Токен: %s", token)

    req = HTTPXRequest(connect_timeout=20, read_timeout=20)
    application = (
        ApplicationBuilder()
        .token(token)
        .request(req)
        .build()
    )

    # Регистрируем команды /start, /mygroups и /myid
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mygroups", mygroups))
    application.add_handler(CommandHandler("myid", myid))

    logger.info("Бот запущен. Начинаем polling.")
    application.run_polling()


if __name__ == '__main__':
    main()
