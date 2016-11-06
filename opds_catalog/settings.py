import logging
import os
from django.conf import settings

sopds_version = '0.30a'
loglevels={'debug':logging.DEBUG,'info':logging.INFO,'warning':logging.WARNING,'error':logging.ERROR,'critical':logging.CRITICAL,'none':logging.NOTSET}

VERSION = "0.31"

# Main SOPDS Book Collection Directory
ROOT_LIB = getattr(settings, "SOPDS_ROOT_LIB", "books/")
BOOK_EXTENSIONS = getattr(settings, "SOPDS_BOOK_EXTESIONS", ['.pdf', '.djvu', '.fb2', '.epub'])

# Количество выдаваемых строк на одну страницу
MAXITEMS = getattr(settings, "SOPDS_MAXITEMS", 60)
DOUBLES_HIDE = getattr(settings, "SOPDS_DOUBLES_HIDE", True)
FB2PARSE = getattr(settings, "SOPDS_FB2PARSE", True)
FB2HSIZE = getattr(settings, "SOPDS_FB2HSIZE", 0)
EPUB2PARSE = getattr(settings, "SOPDS_EPUB2PARSE", False)
COVER_SHOW = getattr(settings, "SOPDS_COVER_SHOW", True)
ZIPSCAN = getattr(settings, "SOPDS_ZIPSCAN", True)
ZIPRESCAN = getattr(settings, "SOPDS_ZIPRESCAN", False)
ZIPCODEPAGE = getattr(settings, "SOPDS_ZIPCODEPAGE", "cp866")
DELETE_LOGICAL = getattr(settings, "SOPDS_DELETE_LOGICAL", False)
SPLITITEMS = getattr(settings, "SOPDS_SPLITITEMS", 300)
FB2TOEPUB = getattr(settings, "SOPDS_FB2TOEPUB", "")
FB2TOMOBI = getattr(settings, "SOPDS_FB2TOMOBI", "")
TEMP_DIR = getattr(settings, "SOPDS_TEMP_DIR", "/tmp")
SINGLE_COMMIT = getattr(settings, "SOPDS_SINGLE_COMMIT", True)
TITLE_AS_FILENAME = getattr(settings, "SOPDS_TITLE_AS_FILENAME", True)
ALPHABET_MENU = getattr(settings, "SOPDS_ALPHABET_MENU", True)
BOOK_SHELF = getattr(settings, "SOPDS_BOOK_SHELF", True)
NOCOVER_PATH = getattr(settings, "SOPDS_NOCOVER_PATH", os.path.join(settings.BASE_DIR,'static/images/nocover.jpg'))
AUTH = getattr(settings, "SOPDS_AUTH", False)
SERVER_LOG = getattr(settings, "SOPDS_SERVER_LOG", os.path.join(settings.BASE_DIR,'log/sopds_server.log'))
SCANNER_LOG = getattr(settings, "SOPDS_SCANNER_LOG", os.path.join(settings.BASE_DIR,'log/sopds_scanner.log'))
SCAN_SHED_MIN = getattr(settings, "SOPDS_SCAN_SHED_MIN", '0')
SCAN_SHED_HOUR = getattr(settings, "SOPDS_SCAN_SHED_HOUR", '0')
SCAN_SHED_DAY = getattr(settings, "SOPDS_SCAN_SHED_DAY", '*')
SCAN_SHED_DOW = getattr(settings, "SOPDS_SCAN_SHED_DOW", '*')

TITLE = getattr(settings, "SOPDS_TITLE", "SimpleOPDS")
SUBTITLE = getattr(settings, "SOPDS_SUBTITLE", "SimpleOPDS Catalog by www.sopds.ru. Version %s."%sopds_version)
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
