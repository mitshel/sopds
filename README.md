#### Simple OPDS Catalog - Простой OPDS Каталог  
#### Author: Dmitry V.Shelepnev  
#### Версия 0.3


## Зависимости проекта
- Django 1.9 
    - в Django 1.8 в django.utils.feedgenerator.Atom1Feed не работает задание заголовка content_type

    
## Установка
	pip install -r requirements.txt

## Инициализация базы данных MySQL.
Во первых для работы каталога необходимо создать базу данных "sopds" и пользователя с необходимыми правами,
например следующим образом:

	mysql -uroot -proot_pass mysql  
	mysql > create database if not exists sopds default charset=utf8;  
	mysql > grant all on sopds.* to 'sopds'@'localhost' identified by 'sopds';  
	mysql > commit;  
	mysql > ^C  

## Настраиваем ./sopds/settings.py

	SOPDS_ROOT_LIB = < Путь к каталогу с книгами >
	SOPDS_AUTH = < False | True >
	SOPDS_SCAN_SHED_MIN  = '0'
	SOPDS_SCAN_SHED_HOUR = '0'

## Готовим базу данных
	python manage.py migrate
	python manage.py createsuperuser (admin:ma*ka)
	python manage.py sopds_util --clear

## Вручную запускаем разовое сканирование коллекции книг
	manage.py sopds_scanner scan

## Запускаем http/opds сервер
	manage.py sopds_server start --daemon

