import logging
import os
from django.conf import settings
from constance import config

loglevels={'debug':logging.DEBUG,'info':logging.INFO,'warning':logging.WARNING,'error':logging.ERROR,'critical':logging.CRITICAL,'none':logging.NOTSET}

VERSION = "0.40"
TITLE = getattr(settings, "SOPDS_TITLE", "SimpleOPDS")
SUBTITLE = getattr(settings, "SOPDS_SUBTITLE", "SimpleOPDS Catalog by www.sopds.ru. Version %s."%VERSION)
ICON = getattr(settings, "SOPDS_ICON", "/static/images/favicon.ico")

loglevel = getattr(settings, "SOPDS_LOGLEVEL", "info")
if loglevel.lower() in loglevels:
    LOGLEVEL=loglevels[loglevel.lower()]
else:
    LOGLEVEL=logging.NOTSET
    
    
def constance_update_all():
    pass
    
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
