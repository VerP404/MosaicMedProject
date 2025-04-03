import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

TARGET_URL = os.getenv("DAGSTER_WO_URL", "http://10.36.0.142:9000/")
DEFAULT_BROWSER = os.getenv("DAGSTER_WO_BROWSER", "firefox")
USERNAME = os.getenv("DAGSTER_WO_USER", "default_user")
PASSWORD = os.getenv("DAGSTER_WO_PASSWORD", "default_password")
