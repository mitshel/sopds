Simple OPDS Catalog
Простой OPDS Каталог
Author Dmitry V.Shelepnev
Версия 0.01a

1. Установка:
Для работы скрипта sopds-scan.py необходимо установить следующие зависимости:
yum install mysql
yum install python3
yum install mysql-connector-python3

2. Конфигурационный файл:
Перед началом работы необходимо внести необходимые настройки в файл конфигурации ./conf/sopds.conf

3. Инициализация базы данных
Для работы каталога необходимо создать базу данных sopds при помощи скрипта:
mysql mysql < ./db/dbcrea.sql

4. Сканирование каталога с книгами
Для скаирования каталога с электронными книгами запустить скрипт sopds-scan.py

5. Доступ к OPDS каталогу через WWW
Для сервера Apache необходимо разрешить запуск cgi-скрипта ./py/sopds.cgi
при помощи директивы, помещенной в .htacess:
Options ExecCGI
или
Options +ExecCGI

6. Использование OPDS каталога с устройств поддерживающих OPDS
Ввести OPDS каталог и следующий URL: your_domain_name/opds/py/sopds.cgi
