import logging
import os
from django.conf import settings

loglevels={'debug':logging.DEBUG,'info':logging.INFO,'warning':logging.WARNING,'error':logging.ERROR,'critical':logging.CRITICAL,'none':logging.NOTSET}

VERSION = "0.35"

# ROOT_LIB содержит путь к каталогу в котором расположена ваша коллекция книг
ROOT_LIB = getattr(settings, "SOPDS_ROOT_LIB", "books/")

# Списк форматов книг, которые будут включаться в каталог
BOOK_EXTENSIONS = getattr(settings, "SOPDS_BOOK_EXTESIONS", ['.pdf', '.djvu', '.fb2', '.epub'])

# Скрывает, найденные дубликаты в выдачах книг
DOUBLES_HIDE = getattr(settings, "SOPDS_DOUBLES_HIDE", True)

# Извлекать метаинформацию из книг fb2
FB2PARSE = getattr(settings, "SOPDS_FB2PARSE", True)

# cover_show - способ показа обложек:
# False - не показывать, 
# True - извлекать обложки на лету и показывать 
COVER_SHOW = getattr(settings, "SOPDS_COVER_SHOW", True)

# ZIPSCAN = True  - Приводит к сканированию файлов архива
ZIPSCAN = getattr(settings, "SOPDS_ZIPSCAN", True)

# Указываем какая кодировка для названий файлов используется в ZIP-архивах
# доступные кодировки: cp437, cp866, cp1251, utf-8
# по умолчанию применяется кодировка cp437
# Поскольку в самом ZIP архиве сведения о кодировке, в которой находятся имена файлов - отсутствуют
# то автоматически определить правильную кодировку для имен файлов не представляется возможным
# поэтому для того чтобы кириллические имена файлов не ваыглядели как крякозябры следует применять кодировку cp866
# по умолчанию также используется значение zip_codepage = cp866
ZIPCODEPAGE = getattr(settings, "SOPDS_ZIPCODEPAGE", "cp866")

# Если INPX_ENABLE = True, то при обнаружении INPX файла в каталоге, сканер не сканирует его содержимое вместе с подгаталогами, а загружает
# данные из найденного INPX файла. Сканер считает что сами архивыс книгами расположены в этом же каталоге. 
# Т.е. INPX-файл должен находится именно в папке с архивами книг
INPX_ENABLE = getattr(settings, "SOPDS_INPX_ENABLE", True)

# Если INPX_SKIP_UNCHANGED = True, то сканер пропускает повторное сканирование, если размер INPX не изменялся
INPX_SKIP_UNCHANGED = getattr(settings, "SOPDS_INPX_SKIP_UNCHANGED", True)

# Если INPX_TEST_ZIP = True, то сканер пытается найти описанный в INPX архив. Если какой-то архив не обнаруживается, 
# то сканер не будет добавлять вязанные с ним данные из INPX в базу данных
# соответсвенно, если INPX_TEST_ZIP = False, то никаких проверок сканер не производит, а просто добавляет данные из INPX в БД
# это гораздо быстрее
INPX_TEST_ZIP = getattr(settings, "SOPDS_INPX_TEST_ZIP", False)

# Если INPX_TEST_FILES = True, то сканер пытается найти описанный в INPX конкретный файл с книгой (уже внутри архивов). Если какой-то файл не обнаруживается, 
# то сканер не будет добавлять эту книгу в базу данных
# соответсвенно, если INPX_TEST_FILES = False, то никаких проверок сканер не производит, а просто добавляет книгу из INPX в БД
# это гораздо быстрее
INPX_TEST_FILES = getattr(settings, "SOPDS_TEST_FILES", False)

# Установка DELETE_LOGICAL=True приведет к тому, что при обнаружении сканером, что книга удалена, запись в БД об этой книге будет удалена логически (avail=0)
# Если DELETE_LOGICAL=False, то произойдет физическое удаление таких записей из базы данных
# пока работает только DELETE_LOGICAL = False
DELETE_LOGICAL = getattr(settings, "SOPDS_DELETE_LOGICAL", False)

SPLITITEMS = getattr(settings, "SOPDS_SPLITITEMS", 300)

# Количество выдаваемых результатов на одну страницу
MAXITEMS = getattr(settings, "SOPDS_MAXITEMS", 60)

# FB2TOEPUB и FB2TOMOBI задают пути к програмам - конвертерам из FB2 в EPUB и MOBI
FB2TOEPUB = getattr(settings, "SOPDS_FB2TOEPUB", "")
FB2TOMOBI = getattr(settings, "SOPDS_FB2TOMOBI", "")

# TEMP_DIR задает путь к временному каталогу, который используется для копирования оригинала и результата конвертации
TEMP_DIR = getattr(settings, "SOPDS_TEMP_DIR", os.path.join(settings.BASE_DIR,'tmp'))

# При скачивании вместо оригинального имени файла книги выдает транслитерацию названия книги
TITLE_AS_FILENAME = getattr(settings, "SOPDS_TITLE_AS_FILENAME", True)

# Включение дополнительного меню выбора алфавита
ALPHABET_MENU = getattr(settings, "SOPDS_ALPHABET_MENU", True)

# Обложка, которая будет демонстрироваться для книг без обложек
NOCOVER_PATH = getattr(settings, "SOPDS_NOCOVER_PATH", os.path.join(settings.BASE_DIR,'static/images/nocover.jpg'))

# Включение BASIC - авторизации
AUTH = getattr(settings, "SOPDS_AUTH", False)

# параметры SERVER_LOG и SCANNER_LOG задают размещение LOG файлов этих процессов
SERVER_LOG = getattr(settings, "SOPDS_SERVER_LOG", os.path.join(settings.BASE_DIR,'opds_catalog/log/sopds_server.log'))
SCANNER_LOG = getattr(settings, "SOPDS_SCANNER_LOG", os.path.join(settings.BASE_DIR,'opds_catalog/log/sopds_scanner.log'))

# параметры SERVER_PID и SCANNER_PID задают размещение PID файлов этих процессов при демонизации
SERVER_PID = getattr(settings, "SOPDS_SERVER_PID", os.path.join(settings.BASE_DIR,'opds_catalog/tmp/sopds_server.pid'))
SCANNER_PID = getattr(settings, "SOPDS_SCANNER_PID", os.path.join(settings.BASE_DIR,'opds_catalog/tmp/sopds_scanner.pid'))

# SCAN_SHED устанавливают значения шедулера, для периодического сканирования коллекции книг
# при помощи manage.py sopds_scanner ...
# Возможные значения можно найти на следующей странице; 
# https://apscheduler.readthedocs.io/en/latest/modules/triggers/cron.html#module-apscheduler.triggers.cron
SCAN_SHED_MIN = getattr(settings, "SOPDS_SCAN_SHED_MIN", '0')
SCAN_SHED_HOUR = getattr(settings, "SOPDS_SCAN_SHED_HOUR", '0')
SCAN_SHED_DAY = getattr(settings, "SOPDS_SCAN_SHED_DAY", '*')
SCAN_SHED_DOW = getattr(settings, "SOPDS_SCAN_SHED_DOW", '*')

TITLE = getattr(settings, "SOPDS_TITLE", "SimpleOPDS")
SUBTITLE = getattr(settings, "SOPDS_SUBTITLE", "SimpleOPDS Catalog by www.sopds.ru. Version %s."%VERSION)
ICON = getattr(settings, "SOPDS_ICON", "/static/images/favicon.ico")

loglevel = getattr(settings, "SOPDS_LOGLEVEL", "info")
if loglevel.lower() in loglevels:
    LOGLEVEL=loglevels[loglevel.lower()]
else:
    LOGLEVEL=logging.NOTSET
    
# Переопределяем некоторые функции для SQLite, которые работают неправлено
from django.db.backends.signals import connection_created
from django.dispatch import receiver

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
