## Перенос данных между разными рабочими машинами

1. Создание бекапа базы данных и создание архива

``` sql
pg_dump -U postgres -d mosaicmed -F p -b -v -f "mosaicmed_backup.sql"
```

2. Перенести файл на сервер и разархиваировать
3. Удалить старую базу данных.
4. Выполнить скрипт

``` sql
psql -U postgres -d mosaicmed -f "C:\Users\RDN\Downloads\Telegram Desktop\mosaicmed_backup.sql"
```
5. Проверить что версия приложения соответствует базе. 
6. Стянуть все изменения из репозитория
```
git pull
```
5. Выполняем миграции

``` python
python manage.py migrate
```

## Установка и настройка postgres на сервере

Выполнить команду для установки PostgreSQL и дополнительных утилит:

``` cmd
sudo apt install postgresql-16 postgresql-contrib
```

Проверяем статус службы с помощью команды:

``` cmd
sudo systemctl status postgresql
```

Если не запущен postgresql, то выполняем:

``` cmd
sudo -u postgres psql
```

Отредактируем файл конфигурации postgresql.conf и измените значение listen_addresses. Проверить версию postgresql и
папку:

``` cmd
sudo nano /etc/postgresql/16/main/postgresql.conf
```

Находим с помощью `ctrl + w` строку:

``` cmd
#listen_addresses = 'localhost'
```

Зменяем на:

``` cmd
listen_addresses = '*'
```

Открываем файл `pg_hba.conf` в той же директории:

``` cmd
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

Внизу файла находи блок `# IPv4 local connections:`
Добавляем в него запись:

``` cmd
host    all             all             0.0.0.0/0               scram-sha-256
```

После внесения изменений перезапускаем PostgreSQL

``` cmd
sudo systemctl restart postgresql
```

Меняем пароль:
Войдем в PostgreSQL

``` 
sudo -u postgres psql
```

Вводим новый пароль.

``` cmd
ALTER USER postgres PASSWORD 'Qaz123';
```
Создаем базу данных
```
CREATE DATABASE mosaicmed;
```
Чтобы закрыть:

``` cmd
\q
```

В системе управления базой данных создаем подключение и базу данных `mosaicmed`

## Настройка проекта

В папке пользователя создаем папку `code`

```
mkdir code
```

Клонируем проект из гит.

```
git clone https://github.com/VerP404/MosaicMedProject.git
```

Переходим в папку `MosaicMedProject`

```
cd MosaicMedProject
```

Устанавливаем виртуальное окружение и активируем его

```
python3.12 -m venv .venv
```

```
source .venv/bin/activate
```

Если выдает ошибки

1. Проверим версию python - должна быть 3.12. Ессли нет, то устанавливаем.

```
python3 --version
```

2. Устанавливаем пакет venv

```
sudo apt update
sudo apt install python3.12-venv
```

После активации `venv` устанавливаем зависимости для проекта

```
pip install -r requirements/base.txt
```

Создаем и редактируем файл .env в корне приложения MosaicMedProject

```  cmd
touch .env
```

``` cmd
nano .env
```

Указываем локальные настройки.

## Переносим базу данных из рабочего проекта

Создаем архив с базой данных `.rar` и передаем его на сервер

``` 
scp "mosaicmed_backup.rar" admindd@10.236.176.150:/home/admindd/code/MosaicMedProject
```

Если не работает, то используем `pscp` из комплекта PuTTY.
Переходим в директорию где установлен PuTTY с файлом `pscp.exe` и выполняем.

```
.\pscp.exe "C:\Users\RDN\Desktop\mosaicmed_backup.rar" admindd@10.236.176.150:/home/admindd/code/MosaicMedProject

```

Для просмотра пути к файлу:

``` cmd
pwd
```

Указываем нужного пользователя, адрес и папку проекта

Устанавливаем архиватор

``` 
sudo apt install unrar
```

Разархивируем файл

``` 
unrar x mosaicmed_backup.rar
```

Разворачиваем бекап.

``` cmd
sudo -u postgres psql -d mosaicmed -f "mosaicmed_backup.sql"
```

Если ошибка доступа, то необходимо предоставить пользователю postgres доступ к папкам проекта.
Нужно указать корректные пути.

``` cmd
sudo chmod +x /home/drpay
sudo chmod +x /home/drpay/code
sudo chmod +x /home/drpay/code/MosaicMedProject

```

## Запуск приложения
# Запуск как фоновой задачи `nohup`
Запуск основного проекта
``` cmd
nohup python3.12 manage.py runserver 0.0.0.0:8000 &
```
Запуск аналитической системы
``` cmd
nohup python3.12 apps/analytical_app/index.py &
```
Просмотр работающих процессов
``` sql
ps -ef | grep 'python3.12'
``` 
Для остановки процесса `kill` и id процесса
```
kill
```