import logging
import os
from django.conf import settings
from constance import config

loglevels={'debug':logging.DEBUG,'info':logging.INFO,'warning':logging.WARNING,'error':logging.ERROR,'critical':logging.CRITICAL,'none':logging.NOTSET}

VERSION = "0.40"

# ROOT_LIB содержит путь к каталогу в котором расположена ваша коллекция книг
ROOT_LIB = config.SOPDS_ROOT_LIB

# Списк форматов книг, которые будут включаться в каталог
BOOK_EXTENSIONS = config.SOPDS_BOOK_EXTENSIONS.split()

# Скрывает, найденные дубликаты в выдачах книг
DOUBLES_HIDE = config.SOPDS_DOUBLES_HIDE

# Извлекать метаинформацию из книг fb2
FB2PARSE = config.SOPDS_FB2PARSE

# cover_show - способ показа обложек:
# False - не показывать, 
# True - извлекать обложки на лету и показывать 
COVER_SHOW = config.SOPDS_COVER_SHOW

# ZIPSCAN = True  - Приводит к сканированию файлов архива
ZIPSCAN = config.SOPDS_ZIPSCAN

# Указываем какая кодировка для названий файлов используется в ZIP-архивах
# доступные кодировки: cp437, cp866, cp1251, utf-8
# по умолчанию применяется кодировка cp437
# Поскольку в самом ZIP архиве сведения о кодировке, в которой находятся имена файлов - отсутствуют
# то автоматически определить правильную кодировку для имен файлов не представляется возможным
# поэтому для того чтобы кириллические имена файлов не ваыглядели как крякозябры следует применять кодировку cp866
# по умолчанию также используется значение zip_codepage = cp866
ZIPCODEPAGE = config.SOPDS_ZIPCODEPAGE

# Если INPX_ENABLE = True, то при обнаружении INPX файла в каталоге, сканер не сканирует его содержимое вместе с подгаталогами, а загружает
# данные из найденного INPX файла. Сканер считает что сами архивыс книгами расположены в этом же каталоге. 
# Т.е. INPX-файл должен находится именно в папке с архивами книг
INPX_ENABLE = config.SOPDS_INPX_ENABLE

# Если INPX_SKIP_UNCHANGED = True, то сканер пропускает повторное сканирование, если размер INPX не изменялся
INPX_SKIP_UNCHANGED = config.SOPDS_INPX_SKIP_UNCHANGED

# Если INPX_TEST_ZIP = True, то сканер пытается найти описанный в INPX архив. Если какой-то архив не обнаруживается, 
# то сканер не будет добавлять вязанные с ним данные из INPX в базу данных
# соответсвенно, если INPX_TEST_ZIP = False, то никаких проверок сканер не производит, а просто добавляет данные из INPX в БД
# это гораздо быстрее
INPX_TEST_ZIP = config.SOPDS_INPX_TEST_ZIP

# Если INPX_TEST_FILES = True, то сканер пытается найти описанный в INPX конкретный файл с книгой (уже внутри архивов). Если какой-то файл не обнаруживается, 
# то сканер не будет добавлять эту книгу в базу данных
# соответсвенно, если INPX_TEST_FILES = False, то никаких проверок сканер не производит, а просто добавляет книгу из INPX в БД
# это гораздо быстрее
INPX_TEST_FILES = config.SOPDS_INPX_TEST_FILES

# Установка DELETE_LOGICAL=True приведет к тому, что при обнаружении сканером, что книга удалена, запись в БД об этой книге будет удалена логически (avail=0)
# Если DELETE_LOGICAL=False, то произойдет физическое удаление таких записей из базы данных
# пока работает только DELETE_LOGICAL = False
DELETE_LOGICAL = config.SOPDS_DELETE_LOGICAL

SPLITITEMS = config.SOPDS_SPLITITEMS

# Количество выдаваемых результатов на одну страницу
MAXITEMS = config.SOPDS_MAXITEMS

# FB2TOEPUB и FB2TOMOBI задают пути к програмам - конвертерам из FB2 в EPUB и MOBI
FB2TOEPUB = config.SOPDS_FB2TOEPUB
FB2TOMOBI = config.SOPDS_FB2TOMOBI

# TEMP_DIR задает путь к временному каталогу, который используется для копирования оригинала и результата конвертации
TEMP_DIR = config.SOPDS_TEMP_DIR

# При скачивании вместо оригинального имени файла книги выдает транслитерацию названия книги
TITLE_AS_FILENAME = config.SOPDS_TITLE_AS_FILENAME

# Включение дополнительного меню выбора алфавита
ALPHABET_MENU = config.SOPDS_ALPHABET_MENU

# Обложка, которая будет демонстрироваться для книг без обложек
NOCOVER_PATH = config.SOPDS_NOCOVER_PATH

# Включение BASIC - авторизации
AUTH = config.SOPDS_AUTH

# параметры SERVER_LOG и SCANNER_LOG задают размещение LOG файлов этих процессов
SERVER_LOG = config.SOPDS_SERVER_LOG
SCANNER_LOG = config.SOPDS_SCANNER_LOG

# параметры SERVER_PID и SCANNER_PID задают размещение PID файлов этих процессов при демонизации
SERVER_PID = config.SOPDS_SERVER_PID
SCANNER_PID = config.SOPDS_SCANNER_PID

# SCAN_SHED устанавливают значения шедулера, для периодического сканирования коллекции книг
# при помощи manage.py sopds_scanner ...
# Возможные значения можно найти на следующей странице; 
# https://apscheduler.readthedocs.io/en/latest/modules/triggers/cron.html#module-apscheduler.triggers.cron
SCAN_SHED_MIN = config.SOPDS_SCAN_SHED_MIN
SCAN_SHED_HOUR = config.SOPDS_SCAN_SHED_HOUR
SCAN_SHED_DAY = config.SOPDS_SCAN_SHED_DAY
SCAN_SHED_DOW = config.SOPDS_SCAN_SHED_DOW

TITLE = getattr(settings, "SOPDS_TITLE", "SimpleOPDS")
SUBTITLE = getattr(settings, "SOPDS_SUBTITLE", "SimpleOPDS Catalog by www.sopds.ru. Version %s."%VERSION)
ICON = getattr(settings, "SOPDS_ICON", "/static/images/favicon.ico")

loglevel = getattr(settings, "SOPDS_LOGLEVEL", "info")
if loglevel.lower() in loglevels:
    LOGLEVEL=loglevels[loglevel.lower()]
else:
    LOGLEVEL=logging.NOTSET
    
# Отработка изменения конфигурации    
import sys
from constance.signals import config_updated
from django.dispatch import receiver

@receiver(config_updated)
def constance_updated(sender, updated_key, new_value, **kwargs):
    if updated_key == 'SOPDS_BOOK_EXTENSIONS':
        value = new_value.split()
    else:
        value = new_value
    key=updated_key.replace('SOPDS_','')
    setattr(sys.modules[__name__], key, value)
 
def constance_update_shedules():
    setattr(sys.modules[__name__], 'SCAN_SHED_MIN', config.SOPDS_SCAN_SHED_MIN)
    setattr(sys.modules[__name__], 'SCAN_SHED_HOUR', config.SOPDS_SCAN_SHED_HOUR)
    setattr(sys.modules[__name__], 'SCAN_SHED_DAY', config.SOPDS_SCAN_SHED_DAY)
    setattr(sys.modules[__name__], 'SCAN_SHED_DOW', config.SOPDS_SCAN_SHED_DOW)   

def constance_update_all():
    pass
    
# Переопределяем некоторые функции для SQLite, которые работают неправлено
from django.db.backends.signals import connection_created

def sopds_upper(s):
    return s.upper()

def sopds_substring(s,i,l):
    i = i - 1
    return s[i:i+l]

def sopds_concat(s1='',s2='',s3=''):
    return "%s%s%s"%(s1,s2,s3)

@receiver(connection_created)
def extend_sqlite(connection=None, **kwargs):
    if connection.vendor == "sqlite":
        connection.connection.create_function('upper',1,sopds_upper)
        connection.connection.create_function('substring',3,sopds_substring)
        connection.connection.create_function('concat',3,sopds_concat)
