#### Simple OPDS Catalog - Простой OPDS Каталог  
#### Author: Dmitry V.Shelepnev  
#### Версия 0.3


## Зависимости проекта
- Django 1.9 
    - в Django 1.8 в django.utils.feedgenerator.Atom1Feed не работает задание заголовка content_type

    
## Установка
pip install -r requirements.txt
manage.py migrate
manage.py createsuperuser (admin:ma*ka)

## Настраиваем ./sopds/settings.py
SOPDS_ROOT_LIB = < Путь к каталогу с книгами >
SOPDS_AUTH = < False | True >

## Готовим базу данных
manage.py sopds_util --clear

## Вручную запускаем сканирование коллекции книг
manage.py sopds_scanner --scan

## Запускаем http/opds сервер
manage.py sopds_server start --daemon

