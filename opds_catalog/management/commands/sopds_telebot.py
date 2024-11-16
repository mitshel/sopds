import os
import signal
import sys
import logging
import re

import json

from collections import OrderedDict
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.conf import settings as main_settings
from django.utils.html import strip_tags
from django.db.models import Q, Count, Max
from django.db import transaction, connection, connections
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.utils import translation

from django.contrib.postgres.aggregates import StringAgg

from opds_catalog.models import Book
from opds_catalog import settings, dl
from opds_catalog.opds_paginator import Paginator as OPDS_Paginator
from sopds_web_backend.settings import HALF_PAGES_LINKS
from constance import config
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import InvalidToken, BadRequest

query_delimiter = "####"

def cmdtrans(func):
    def wrapper(self, update: Update, context: CallbackContext):
        translation.activate(config.SOPDS_LANGUAGE)
        result =  func(self, update, context)
        translation.deactivate()
        return result

    return wrapper


def check_auth_decorator(func):
    def wrapper(self, update: Update, context: CallbackContext):
        if not config.SOPDS_TELEBOT_AUTH:
            return func(self, update, context)

        if connection.connection and not connection.is_usable():
            del(connections._connections.default)

        query = update.message if update.message else update.callback_query.message
        username = update.message.from_user.username if update.message else update.callback_query.from_user.username
        users = User.objects.filter(username__iexact=username)

        if users and users[0].is_active:
            return func(self, update, context)

        context.bot.sendMessage(chat_id=query.chat_id,
                        text=_("Hello %s!\nUnfortunately you do not have access to information. Please contact the bot administrator.") % username)
        self.logger.info(_("Denied access for user: %s") % username)

        return None

    return wrapper

class Command(BaseCommand):
    help = 'SimpleOPDS Telegram Bot engine.'

    # The above code is creating a variable named "query_cache".
    query_cache = OrderedDict()
    query_cache_max_size = 10
    query_cache_max_age = timedelta(days = 2)

    can_import_settings = True
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument('command', help='Use [ start | stop | restart ]')
        parser.add_argument('--verbose',action='store_true', dest='verbose', default=False, help='Set verbosity level for SimpleOPDS telebot.')
        parser.add_argument('--daemon',action='store_true', dest='daemonize', default=False, help='Daemonize server')
        return None

    def handle(self, *args, **options):
        self.pidfile = os.path.join(main_settings.BASE_DIR, config.SOPDS_TELEBOT_PID)
        action = options['command']
        self.logger = logging.getLogger('')
        self.logger.setLevel(logging.DEBUG)
        formatter=logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')

        if settings.LOGLEVEL!=logging.NOTSET:
            # Создаем обработчик для записи логов в файл
            fh = logging.FileHandler(config.SOPDS_TELEBOT_LOG)
            fh.setLevel(settings.LOGLEVEL)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

        if options['verbose']:
            # Создадим обработчик для вывода логов на экран с максимальным уровнем вывода
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        if (options["daemonize"] and (action in ["start"])):
            if sys.platform == "win32":
                self.stdout.write("On Windows platform Daemonize not working.")
            else:
                daemonize()

        if action == "start":
            self.start()
        elif action == "stop":
            pid = open(self.pidfile, "r").read()
            self.stop(pid)
        elif action == "restart":
            pid = open(self.pidfile, "r").read()
            self.restart(pid)
        return None

    @cmdtrans
    @check_auth_decorator
    def startCommand(self, update: Update, context: CallbackContext):
        context.bot.sendMessage(chat_id=update.message.chat_id, text=_("%(subtitle)s\nHello %(username)s! To search for a book, enter part of her title or author:")%
                                                             {'subtitle':settings.SUBTITLE,'username':update.message.from_user.username})
        self.logger.info("Start talking with user: %s"%update.message.from_user)
        return None

    def bookFilter(self, query):
        if connection.connection and not connection.is_usable():
            del(connections._connections.default)
        if query in self.query_cache:
            self.query_cache.move_to_end(query)
            timestamp, books = self.query_cache[query]
            if datetime.now() - timestamp <= self.query_cache_max_age:
                return books
            else:
                self.logger.info("Query '%s' is too old in query cache."%query)
        q_objects = Q()
        q_objects.add(Q(search_title__contains=query.upper()), Q.OR)
        q_objects.add( Q(authors__search_full_name__contains=query.upper()), Q.OR)
        books = Book.objects.filter(q_objects).annotate(authors_set=StringAgg("authors__full_name", delimiter=", "))
        if config.SOPDS_DOUBLES_HIDE:
            books = books.values("title", "search_title", "authors_set").annotate(doubles=Count("filename"), id=Max("id")).order_by("search_title").distinct()
        else:
            books = books.values("title", "search_title", "authors_set", "id", "docdate").order_by('search_title', '-docdate').distinct()
        self.query_cache[query] = datetime.now(), books
        #self.logger.info("Query '%s' is added to query cache."%query)
        if len(self.query_cache) > self.query_cache_max_size:
            query_old, _books_old = self.query_cache.popitem(0)
            self.logger.info("Query cache is overloaded. Query '%s' is removed from query cache."%query_old)

        return books

    def bookPager(self, books, page_num, query):
        # as I can understand, len de-facto reads all items in memory or QuerySet cache
        books_count = len(books)
        op = OPDS_Paginator(books_count, 0, page_num, config.SOPDS_TELEBOT_MAXITEMS, HALF_PAGES_LINKS)
        summary_doubles = config.SOPDS_DOUBLES_HIDE

        start = op.d1_first_pos if (op.d1_first_pos == 0) else op.d1_first_pos - 1
        finish = op.d1_last_pos

        response = ''
        for b in books[start:finish + 1]:
            doubles = _("(doubles:%s) ")%b['doubles'] if summary_doubles and b['doubles'] else ''
            response+='<b>%(title)s</b>\n%(author)s\n%(dbl)s/download%(link)s\n\n'%{'title':b['title'], 'author':b['authors_set'],'link':b['id'], 'dbl':doubles}

        #fix for rare empty response
        if response:
            buttons = [InlineKeyboardButton('1 <<', callback_data='%s%s%s'%(query,query_delimiter,1)),
                    InlineKeyboardButton('%s <'%op.previous_page_number , callback_data='%s%s%s'%(query,query_delimiter,op.previous_page_number)),
                    InlineKeyboardButton('[ %s ]'%op.number , callback_data='%s%s%s'%(query,query_delimiter,'current')),
                    InlineKeyboardButton('> %s'%op.next_page_number , callback_data='%s%s%s'%(query,query_delimiter,op.next_page_number)),
                    InlineKeyboardButton('>> %s'%op.num_pages, callback_data='%s%s%s'%(query,query_delimiter,op.num_pages))]
            markup = InlineKeyboardMarkup([buttons]) if op.num_pages>1 else None
            return {'message':response, 'buttons':markup}
        else:
            return self.bookPager(books, page_num - 1, query)

    @cmdtrans
    @check_auth_decorator
    def getBooks(self, update: Update, context: CallbackContext):
        query=update.message.text
        self.logger.info("Got message from user %s: %s" % (update.message.from_user.username, query))

        if len(query)<3:
            response = _("Too short for search, please try again.")
        else:
            response = _("I'm searching for the book: %s") % (query)

        context.bot.send_message(chat_id=update.message.chat_id, text=response)
        self.logger.info("Send message to user %s: %s" % (update.message.from_user.username,response))

        if len(query) < 3:
            return None

        books = self.bookFilter(query)
        #books_count = books.count()
        # as I can understand, len de-facto reads all items in memory or QuerySet cache
        books_count = len(books)

        if books_count == 0:
            response = _("No results were found for your query, please try again.")
            context.bot.send_message(chat_id=update.message.chat_id, text=response)
            self.logger.info("Send message to user %s: %s" % (update.message.from_user.username,response))
            return

        response = _("Found %s books.\nI create list, after a few seconds, select the file to download:") % books_count
        context.bot.send_message(chat_id=update.message.chat_id, text=response)
        self.logger.info("Send message to user %s: %s" % (update.message.from_user.username, response))

        response = self.bookPager(books, 1, query)
        context.bot.send_message(chat_id=update.message.chat_id, text=response['message'], parse_mode='HTML', reply_markup=response['buttons'])
        return None

    @cmdtrans
    @check_auth_decorator
    def getBooksPage(self, update: Update, context: CallbackContext):
        callback_query = update.callback_query
        (query,page_num) = callback_query.data.split(query_delimiter, maxsplit=1)
        if (page_num == 'current'):
            return
        try:
            page_num = int(page_num)
        except:
            page_num = 1

        books = self.bookFilter(query)
        response = self.bookPager(books, page_num, query)
        try:
            context.bot.edit_message_text(chat_id=callback_query.message.chat_id, message_id=callback_query.message.message_id, text=response['message'], parse_mode='HTML', reply_markup=response['buttons'])
        except BadRequest:
            pass
        return None

    @cmdtrans
    @check_auth_decorator
    def downloadBooks(self, update: Update, context: CallbackContext):
        book_id_set=re.findall(r'\d+$',update.message.text)
        if len(book_id_set)==1:
            try:
                book_id=int(book_id_set[0])
                book=Book.objects.get(id=book_id)
            except:
                book_id = None
                book=None
        else:
            book_id=None
            book=None

        if book==None:
            response = _("The book on the link you specified is not found, try to repeat the book search first.")
            context.bot.sendMessage(chat_id=update.message.chat_id, text=response, parse_mode='HTML')
            self.logger.info("Not find download links: %s" % response)
            return

        authors = ', '.join([a['full_name'] for a in book.authors.values()])
        response = ('<b>%(title)s</b>\n%(author)s\n<b>'+_("Annotation:")+'</b>%(annotation)s\n') % {'title': book.title, 'author': authors, 'annotation':book.annotation}

        buttons = [InlineKeyboardButton(book.format.upper(), callback_data='/getfileorig%s'%book_id)]
        if book.format not in settings.NOZIP_FORMATS:
            buttons += [InlineKeyboardButton(book.format.upper()+'.ZIP', callback_data='/getfilezip%s'%book_id)]
        if (config.SOPDS_FB2TOEPUB != "") and (book.format == 'fb2'):
            buttons += [InlineKeyboardButton('EPUB', callback_data='/getfileepub%s'%book_id)]
        if (config.SOPDS_FB2TOMOBI != "") and (book.format == 'fb2'):
            buttons += [InlineKeyboardButton('MOBI', callback_data='/getfilemobi%s'%book_id)]

        markup = InlineKeyboardMarkup([buttons])
        context.bot.sendMessage(chat_id=update.message.chat_id, text=response, parse_mode='HTML', reply_markup=markup)
        self.logger.info("Send download buttons.")
        return None

    @cmdtrans
    @check_auth_decorator
    def getBookFile(self, update: Update, context: CallbackContext):
        callback_query = update.callback_query
        query = callback_query.data
        book_id_set=re.findall(r'\d+$',query)
        if len(book_id_set)==1:
            try:
                book_id=int(book_id_set[0])
                book=Book.objects.get(id=book_id)
            except:
                book=None
        else:
            book_id=None
            book=None

        if book==None:
            response = _("The book on the link you specified is not found, try to repeat the book search first.")
            context.bot.sendMessage(chat_id=callback_query.message.chat_id, text=response, parse_mode='HTML')
            self.logger.info("Not find download links: %s" % response)
            return

        filename = dl.getFileName(book)
        document = None

        if re.match(r'/getfileorig',query):
            document = dl.getFileData(book)

        if re.match(r'/getfilezip',query):
            document = dl.getFileDataZip(book)
            filename = filename + '.zip'

        if re.match(r'/getfileepub',query):
            document = dl.getFileDataEpub(book)
            filename = filename.replace('.fb2', '.epub')

        if re.match(r'/getfilemobi',query):
            document = dl.getFileDataMobi(book)
            filename = filename.replace('.fb2', '.mobi')

        if document:
            context.bot.send_document(chat_id=callback_query.message.chat_id,document=document,filename=filename)
            document.close()
            self.logger.info("Send file: %s" % filename)
        else:
            response = _("There was a technical error, please contact the Bot administrator.")
            context.bot.sendMessage(chat_id=callback_query.message.chat_id, text=response, parse_mode='HTML')
            self.logger.info("Book get error: %s" % response)

        return None

    @cmdtrans
    @check_auth_decorator
    def botCallback(self, update: Update, context: CallbackContext):
        query = update.callback_query

        if re.match(r'/getfile', query.data):
            return self.getBookFile(update, context)
        else:
            return self.getBooksPage(update, context)

    def start(self):
        writepid(self.pidfile)
        quit_command = 'CTRL-BREAK' if sys.platform == 'win32' else 'CONTROL-C'
        self.stdout.write("Quit the sopds_telebot with %s.\n"%quit_command)
        try:
            updater = Updater(token=config.SOPDS_TELEBOT_API_TOKEN)
            start_command_handler = CommandHandler('start', self.startCommand)
            get_book_handler = MessageHandler(Filters.text, self.getBooks)
	    #fix deprecated RegexHandler See https://git.io/fxJuV for more info
            download_handler = MessageHandler(Filters.regex('^/download\d+$'),self.downloadBooks)

            updater.dispatcher.add_handler(start_command_handler)
	    #change order of handlers, to handle download(regexp) before common text(book name)
            updater.dispatcher.add_handler(download_handler)
            updater.dispatcher.add_handler(get_book_handler)
            updater.dispatcher.add_handler(CallbackQueryHandler(self.botCallback))

            updater.start_polling(drop_pending_updates=True)
            updater.idle()
        except InvalidToken:
            self.stdout.write('Invalid telegram token.\nSet correct token for telegram API by command:\n python3 manage.py sopds_util setconf SOPDS_TELEBOT_API_TOKEN "<token>"')
            self.logger.error('Invalid telegram token.')

        except (KeyboardInterrupt, SystemExit):
            pass

        return None

    def stop(self, pid):
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError as e:
            self.stdout.write("Error stopping sopds_telebot: %s"%str(e))
        return None

    def restart(self, pid):
        self.stop(pid)
        self.start()
        return None

def writepid(pid_file):
    """
    Write the process ID to disk.
    """
    fp = open(pid_file, "w")
    fp.write(str(os.getpid()))
    fp.close()

def daemonize():
    """
    Detach from the terminal and continue as a daemon.
    """
    # swiped from twisted/scripts/twistd.py
    # See http://www.erlenstar.demon.co.uk/unix/faq_toc.html#TOC16
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent
    os.setsid()
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent again.
    os.umask(0)

    std_in = open("/dev/null", 'r')
    std_out = open(config.SOPDS_TELEBOT_LOG, 'a+')
    os.dup2(std_in.fileno(), sys.stdin.fileno())
    os.dup2(std_out.fileno(), sys.stdout.fileno())
    os.dup2(std_out.fileno(), sys.stderr.fileno())

    os.close(std_in.fileno())
    os.close(std_out.fileno())
    return None






