### На странице home должны быть сервисы:

* Рабочее место главного врача

Продумать что должно быть тут

* Рабочее место заведующего

Есть заведующие корпусами и отделений в корпусах.
Нужно сделать персональную настройку для заведующего с выбором чекбоксов - список корпусов и подразделений,
которые будут доступны для фильтрации.

* Рабочее место экономиста

Все отчеты по объемам.

* Рабочее место статистика

Статистические отчеты. Часть взять от экономистов.

* Рабочее место врача

Главная страница - дашборд с выполнением показателей и текущими задачами (разработать!).
Доступ к отчетам по врачам (с фильтром по себе).

* Рабочее место модератора

Блоки для загрузки данных. Получение отчетов по ИТ службе. Сборки счетов.

* Администрирование

Доступ в админсайт. Возможно дать часть прав Модератору

* Обучение

Инструкции по работе с системой. Документация. Приказы и прочее.
Сделать на основе wiki-системы. Если есть личный кабинет, то добавить тестирование после темы.

* Панель пациента

Интегрировать в проект информационную панель

* Панель главного врача

Открывается приложение дашборд для телевизора главного врача с основными показателями на 1 страницу

* Инфостенд

Инфомат для каждого корпуса. Для модератора (программиста в МО). Создание кнопок в интерфейсе.
Печать справок. Возможно дополнить функционал - нужно проработать.

* Мониторинг

Система создания и ведения отчетных форм. Нужно сделать аналог Parus. Посмотреть готовые opensource решения.

Рабочие места:

1. Главная страница - дашборд с основными данными нужными специалисту
2. Сайдбар - переход между разными страницами.

Придумать способ разграничения прав. разделять по модулям/отчетам/страницам и в админке разделять или иначе?



## Создание новых страниц отчетов

1. Создаем папку отчета в папке [pages](apps%2Fanalytical_app%2Fpages). Папка создается в нужном блоке.
2. Формат папки: 2 файла page (форматирование) и query (запрос)
3. в main добавляем в CardBody нужные ссылки на отчеты и колбек для маршрутизации
4. Вносим изменения в [routes.py](apps%2Fanalytical_app%2Froutes.py) маршрутизацию как в предыдущем пункте





