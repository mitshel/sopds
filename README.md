Simple OPDS Catalog
Простой OPDS Каталог
Author: Dmitry V.Shelepnev
Версия 0.04

1. Установка:
Для работы скрипта sopds-scan.py необходимо установить следующие зависимости:
yum install mysql
yum install python3
yum install mysql-connector-python3

2. Конфигурационный файл:
Перед началом работы необходимо внести необходимые настройки в файл конфигурации ./conf/sopds.conf

3. Инициализация базы данных
Для работы каталога необходимо создать(пересоздать) базу данных sopds при помощи скрипта:
mysql mysql < ./db/dbcrea.sql

Тоже самое рекомендую сделать при переходе от версии к версии.

4. Сканирование каталога с книгами
Для сканирования каталога с электронными книгами запустить скрипт sopds-scan.py

5. Доступ к OPDS каталогу через WWW
Для сервера Apache необходимо разрешить запуск cgi-скрипта ./py/sopds.cgi
при помощи директивы, помещенной в .htacess:
  Options ExecCGI
или
  Options +ExecCGI

Для ограничения доступа добавьте в .htaccess
  AuthType Basic
  AuthName "SOPDS Library"
  AuthUserFile /home/www/.htpasswd
  require valid-user
Ну и конечно добавить пользователя и пароль в файл /home/www/.htpasswd при помощи утилиты htpasswd


6. Использование OPDS каталога с устройств поддерживающих OPDS
Ввести OPDS каталог и следующий URL: your_domain_name/opds/py/sopds.cgi
