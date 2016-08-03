#### Simple OPDS Catalog - Простой OPDS Каталог  
#### Author: Dmitry V.Shelepnev  
#### Версия 0.3


## Зависимости проекта
- Django 1.9 
    - в Django 1.8 в django.utils.feedgenerator.Atom1Feed не работает задание заголовка content_type

    
## Установка
manage.py migrate
manage.py createsuperuser (admin:ma*ka)

Внести изменения в settings.py
SOPDS_ROOT_LIB = < Путь к каталогу с книгами >
SOPDS_AUTH = < False | True >

manage.py sopds --clear
manage.py sopds --scan

