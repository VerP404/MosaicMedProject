# 🚀 **ПОЛНАЯ ИНСТРУКЦИЯ ПО НАСТРОЙКЕ ПРОЕКТА**

## 🏆 **1. Установка и настройка PostgreSQL на сервере**
### ➡️ Установка PostgreSQL и дополнительных утилит:
```bash
sudo apt update
sudo apt install postgresql-16 postgresql-contrib
```

### ➡️ Проверка статуса службы:
```bash
sudo systemctl status postgresql
```

Если служба не запущена — запустите её:

```bash
sudo systemctl start postgresql
```

### ➡️ Редактирование конфигурационного файла `postgresql.conf`:
Открываем конфиг:
```bash
sudo nano /etc/postgresql/16/main/postgresql.conf
```

Находим строку:
```
#listen_addresses = 'localhost'
```
Изменяем на:
```
listen_addresses = '*'
```

### ➡️ Редактирование конфигурационного файла `pg_hba.conf`:
Открываем файл:
```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

Добавляем внизу строки для доступа по сети:
```
host    all             all             0.0.0.0/0               scram-sha-256
```

### ➡️ Перезапуск PostgreSQL после изменения конфигурации:
```bash
sudo systemctl restart postgresql
```

### ➡️ Установка пароля для пользователя `postgres`:
1. Входим в PostgreSQL:
```bash
sudo -u postgres psql
```
2. Устанавливаем пароль:
```sql
ALTER USER postgres PASSWORD 'Qaz123';
```
3. Выходим из psql:
```bash
\q
```

### ➡️ Создание базы данных:
```sql
CREATE DATABASE mosaicmed;
```

## 🗄️ **2. Перенос базы данных (из бэкапа)**
### 🔹 **1. Создание бэкапа на продакшене**  
Создать папку для бэкапа и выполнить команду:
```bash
sudo -u postgres pg_dump -d mosaicmed -F p -b -v -f "mosaicmed_backup_$(date +%Y%m%d%H%M%S).sql"
```
Для Windows:
```bash
pg_dump -U postgres -d mosaicmed -F p -b -v -f "mosaicmed_backup.sql"
```
Архивируем дамп перед переносом:
```bash
tar -czvf mosaicmed_backup_$(date +%Y%m%d%H%M%S).tar.gz mosaicmed_backup_$(date +%Y%m%d%H%M%S).sql
```
### 🔹 **2. Перенос бэкапа на новый сервер**  
Переносим с помощью `scp`:
```bash
scp "mosaicmed_backup.sql" user@<IP>:/path/to/target/
```
Разархивируем архив:
```bash
tar -xzvf mosaicmed_backup{*}.tar.gz
```
### 🔹 **3. Удаление старой базы**  
Открываем консоль PostgreSQL:
```bash
sudo -u postgres psql
```

Открываем консоль в Windows:
```bash
psql -U postgres -d mosaicmed
```

Удаляем базу:
```sql
DROP DATABASE IF EXISTS mosaicmed;
```

### 🔹 **4. Восстановление базы из бэкапа**  
Выполняем команду для импорта:
```bash
psql -U postgres -d mosaicmed -f "mosaicmed_backup.sql"
```

### 🔹 **5. Проверка работоспособности базы**  
Входим в базу и проверяем содержимое:
```bash
sudo -u postgres psql
```
Проверяем таблицы:
```sql
\dt
```

## 🏗️ **3. Установка проекта**
### 🔹 **1. Клонирование репозитория**  
Переходим в папку для кода:
```bash
mkdir ~/code
cd ~/code
```

Клонируем проект:
```bash
git clone https://github.com/VerP404/MosaicMedProject.git
cd MosaicMedProject
```

### 🔹 **2. Создание и активация виртуального окружения**  
Проверяем установленную версию Python:
```bash
python3 --version
```

Создаём виртуальное окружение:
```bash
python3.12 -m venv .venv
```

Активируем окружение:
```bash
source .venv/bin/activate
```

Если ошибка — установить `venv`:
```bash
sudo apt update
sudo apt install python3.12-venv
```

### 🔹 **3. Установка зависимостей**  
Выполняем установку пакетов:
```bash
pip install -r requirements/base.txt
```

### 🔹 **4. Создание `.env` файла**  
Создаём `.env`:
```bash
touch .env
nano .env
```

Добавляем конфигурацию для базы данных:
```env
DEBUG=True
DATABASE_URL=postgres://postgres:Qaz123@localhost:5432/mosaicmed
```

## 🔥 **4. Запуск проекта**
### ➡️ Выполняем миграции:
```bash
python manage.py makemigrations
python manage.py migrate
```

### ➡️ Создание суперпользователя:
```bash
python manage.py createsuperuser
```

### ➡️ Запуск сервера:
```bash
python manage.py runserver 0.0.0.0:8000
```

## 🏢 **5. Перезапуск Django и аналитического приложения**
### 🔹 Запуск как фонового процесса (`nohup`)  
Запуск основного приложения:
```bash
nohup python3.12 manage.py runserver 0.0.0.0:8000 &
```

Запуск аналитического приложения:
```bash
nohup python3.12 apps/analytical_app/index.py &
```

Проверка запущенных процессов:
```bash
ps -ef | grep 'python3.12'
```

Остановка процесса:
```bash
kill <PID>
```

## 🌐 **6. Настройка Selenium на сервере (Ubuntu)**
### ➡️ Установка необходимых пакетов:
```bash
sudo apt-get update
sudo apt-get install -y wget unzip xvfb google-chrome-stable
```

### ➡️ Установка драйвера Chrome:
```bash
wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
```

### ➡️ Запуск Selenium через `xvfb-run`:
```bash
xvfb-run -a python3.12 manage.py load_data_oms_chrome
```

## 🚀 **1. Установка Chrome и ChromeDriver**

### Windows:
1. Скачайте и установите Chrome версии 114.0.5735.90:
   - https://dl.google.com/chrome/win/114.0.5735.90/chrome_installer.exe

2. Скачайте ChromeDriver версии 114.0.5735.90:
   - https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_win32.zip
   - Распакуйте в `C:\chromedriver\`

3. Установите переменные окружения:
```powershell
$env:CHROME_VERSION="114.0.5735.90"
$env:CHROMEDRIVER_VERSION="114.0.5735.90"
$env:CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
$env:CHROMEDRIVER_PATH="C:\chromedriver\chromedriver.exe"
```

### Linux (Ubuntu):
1. Установите Chrome версии 114.0.5735.90:
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_114.0.5735.90-1_amd64.deb
sudo dpkg -i google-chrome-stable_114.0.5735.90-1_amd64.deb
sudo apt-get install -f
```

2. Установите ChromeDriver версии 114.0.5735.90:
```bash
wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

3. Установите переменные окружения:
```bash
export CHROME_VERSION="114.0.5735.90"
export CHROMEDRIVER_VERSION="114.0.5735.90"
export CHROME_PATH="/usr/bin/google-chrome"
export CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"
```

## 🕒 **2. Добавление в cron**
### Windows:
Создайте задачу в Планировщике задач Windows:
1. Откройте "Планировщик задач"
2. Создайте новую задачу
3. Установите триггер "Ежечасно"
4. Действие: Запустить программу
5. Программа: `C:\path\to\python.exe`
6. Аргументы: `C:\path\to\manage.py load_data_oms_chrome`

### Linux:
Откройте crontab:
```bash
crontab -e
```

Добавьте задачу:
```bash
0 * * * * /path/to/.venv/bin/python /path/to/manage.py load_data_oms_chrome
```

## ✅ **Готово!** 😎
