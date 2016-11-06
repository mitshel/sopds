#### Simple OPDS Catalog - Простой OPDS Каталог  
#### Author: Dmitry V.Shelepnev  
#### Версия 0.32


## Зависимости проекта
- Django 1.8
- Pillow 2.9.0
- apscheduler

## Установка проекта
	pip install -r requirements.txt

## Инициализация базы данных MySQL.
Во первых для работы каталога необходимо создать базу данных "sopds" и пользователя с необходимыми правами,
например следующим образом:

	mysql -uroot -proot_pass mysql  
	mysql > create database if not exists sopds default charset=utf8;  
	mysql > grant all on sopds.* to 'sopds'@'localhost' identified by 'sopds';  
	mysql > commit;  
	mysql > ^C  

## Настраиваем ./sopds/settings.py (настройки в конце файла)

	SOPDS_ROOT_LIB = < Путь к каталогу с книгами >
	SOPDS_AUTH = < False | True >
	SOPDS_SCAN_SHED_MIN  = '0,12'
	SOPDS_SCAN_SHED_HOUR = '0'
    
## Производим инициализацию базы данных и заполнение начальными данными (жанры)
	python manage.py migrate
	python manage.py sopds_util --clear
	
## Cоздаем суперпользователя
	python manage.py createsuperuser
	
## Вручную запускаем разовое сканирование коллекции книг
	manage.py sopds_scanner scan

## Запускаем HTTP/OPDS сервер
	manage.py sopds_server start --daemon
	
## Запускаем SCANNER сервер
	manage.py sopds_scanner start --daemon

