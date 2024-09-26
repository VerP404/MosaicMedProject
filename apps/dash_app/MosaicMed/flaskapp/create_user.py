# create_user.py
from services.MosaicMed.flaskapp.models import User
from database.db_conn import init_db

# Инициализируем базу данных
init_db()


def create_user(username, password, last_name, first_name, middle_name, birth_date, position, role, category):
    User.create(username, password, last_name, first_name, middle_name, birth_date, position, role, category)


if __name__ == "__main__":
    # Создаем пользователя admin
    create_user(
        username="admin",
        password="440856Mo",  # Убедитесь, что используете сильный пароль
        last_name="Родионов",
        first_name="Дмитрий",
        middle_name="Николаевич",
        birth_date="1992-07-26",
        position="Administrator",
        role="admin",
        category="general"
    )
    print("Пользователь создан")
