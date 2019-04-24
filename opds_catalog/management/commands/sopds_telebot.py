import os
import signal
import sys
import logging
import re

from django.core.management.base import BaseCommand
from django.conf import settings as main_settings
from django.utils.html import strip_tags
from django.db.models import Q
from django.db import transaction, connection, connections
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.utils import translation

from opds_catalog.models import Book
from opds_catalog import settings, dl
from opds_catalog.opds_paginator import Paginator as OPDS_Paginator
from sopds_web_backend.settings import HALF_PAGES_LINKS
from constance import config
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import InvalidToken

query_delimiter = "####"

def cmdtrans(func):
    def wrapper(self, bot, update):
        translation.activate(config.SOPDS_LANGUAGE)
        result =  func(self, bot, update)
        translation.deactivate()
        return result

    return wrapper


def CheckAuthDecorator(func):
    def wrapper(self, bot, update):
        if not config.SOPDS_TELEBOT_AUTH:
            return func(self, bot, update)

        if connection.connection and not connection.is_usable():
            del(connections._connections.default)

        query = update.message if update.message else update.callback_query.message
        username = update.message.from_user.username if update.message else update.callback_query.from_user.username
        users = User.objects.filter(username__iexact=username)

        if users and users[0].is_active:
            return func(self, bot, update)

        bot.sendMessage(chat_id=query.chat_id,
                        text=_("Hello %s!\nUnfortunately you do not have access to information. Please contact the bot administrator.") % username)
        self.logger.info(_("Denied access for user: %s") % username)

        return

    return wrapper

class Command(BaseCommand):
    help = 'SimpleOPDS Telegram Bot engine.'
    can_import_settings = True
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument('command', help='Use [ start | stop | restart ]')
        parser.add_argument('--verbose',action='store_true', dest='verbose', default=False, help='Set verbosity level for SimpleOPDS telebot.')
        parser.add_argument('--daemon',action='store_true', dest='daemonize', default=False, help='Daemonize server')
        
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

    @cmdtrans
    @CheckAuthDecorator
    def startCommand(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id, text=_("%(subtitle)s\nHello %(username)s! To search for a book, enter part of her title or author:")%
                                                             {'subtitle':settings.SUBTITLE,'username':update.message.from_user.username})
        self.logger.info("Start talking with user: %s"%update.message.from_user)
        return

    def BookFilter(self, query):
        if connection.connection and not connection.is_usable():
            del(connections._connections.default)

        q_objects = Q()
        q_objects.add(Q(search_title__contains=query.upper()), Q.OR)
        q_objects.add( Q(authors__search_full_name__contains=query.upper()), Q.OR)
        books = Book.objects.filter(q_objects).order_by('search_title', '-docdate').distinct()

        return books

    def BookPager(self, books, page_num, query):
        books_count = books.count()
        op = OPDS_Paginator(books_count, 0, page_num, config.SOPDS_TELEBOT_MAXITEMS, HALF_PAGES_LINKS)
        items = []

        prev_title = ''
        prev_authors_set = set()

        # Начаинам анализ с последнего элемента на предидущей странице, чторбы он "вытянул" с этой страницы
        # свои дубликаты если они есть
        summary_DOUBLES_HIDE = config.SOPDS_DOUBLES_HIDE
        start = op.d1_first_pos if ((op.d1_first_pos == 0) or (not summary_DOUBLES_HIDE)) else op.d1_first_pos - 1
        finish = op.d1_last_pos

        for row in books[start:finish + 1]:
            p = {'doubles': 0, 'lang_code': row.lang_code, 'filename': row.filename, 'path': row.path, \
                 'registerdate': row.registerdate, 'id': row.id, 'annotation': strip_tags(row.annotation), \
                 'docdate': row.docdate, 'format': row.format, 'title': row.title, 'filesize': row.filesize // 1000, \
                 'authors': row.authors.values(), 'genres': row.genres.values(), 'series': row.series.values(),
                 'ser_no': row.bseries_set.values('ser_no')
                 }
            if summary_DOUBLES_HIDE:
                title = p['title']
                authors_set = {a['id'] for a in p['authors']}
                if title.upper() == prev_title.upper() and authors_set == prev_authors_set:
                    items[-1]['doubles'] += 1
                else:
                    items.append(p)
                prev_title = title
                prev_authors_set = authors_set
            else:
                items.append(p)

        # "вытягиваем" дубликаты книг со следующей страницы и удаляем первый элемент который с предыдущей страницы и "вытягивал" дубликаты с текущей
        if summary_DOUBLES_HIDE:
            double_flag = True
            while ((finish + 1) < books_count) and double_flag:
                finish += 1
                if books[finish].title.upper() == prev_title.upper() and {a['id'] for a in books[finish].authors.values()} == prev_authors_set:
                    items[-1]['doubles'] += 1
                else:
                    double_flag = False

            if op.d1_first_pos != 0:
                items.pop(0)

        response = ''
        for b in items:
            authors = ', '.join([a['full_name'] for a in b['authors']])
            doubles = _("(doubles:%s) ")%b['doubles'] if b['doubles'] else ''
            response+='<b>%(title)s</b>\n%(author)s\n%(dbl)s/download%(link)s\n\n'%{'title':b['title'], 'author':authors,'link':b['id'], 'dbl':doubles}

        buttons = [InlineKeyboardButton('1 <<', callback_data='%s%s%s'%(query,query_delimiter,1)),
                   InlineKeyboardButton('%s <'%op.previous_page_number , callback_data='%s%s%s'%(query,query_delimiter,op.previous_page_number)),
                   InlineKeyboardButton('[ %s ]'%op.number , callback_data='%s%s%s'%(query,query_delimiter,'current')),
                   InlineKeyboardButton('> %s'%op.next_page_number , callback_data='%s%s%s'%(query,query_delimiter,op.next_page_number)),
                   InlineKeyboardButton('>> %s'%op.num_pages, callback_data='%s%s%s'%(query,query_delimiter,op.num_pages))]

        markup = InlineKeyboardMarkup([buttons]) if op.num_pages>1 else None

        return {'message':response, 'buttons':markup}

    @cmdtrans
    @CheckAuthDecorator
    def getBooks(self, bot, update):
        query=update.message.text
        self.logger.info("Got message from user %s: %s" % (update.message.from_user.username, query))

        if len(query)<3:
            response = _("Too short for search, please try again.")
        else:
            response = _("I'm searching for the book: %s") % (query)

        bot.send_message(chat_id=update.message.chat_id, text=response)
        self.logger.info("Send message to user %s: %s" % (update.message.from_user.username,response))

        if len(query) < 3:
            return

        books = self.BookFilter(query)
        books_count = books.count()

        if books_count == 0:
            response = _("No results were found for your query, please try again.")
            bot.send_message(chat_id=update.message.chat_id, text=response)
            self.logger.info("Send message to user %s: %s" % (update.message.from_user.username,response))
            return

        response = _("Found %s books.\nI create list, after a few seconds, select the file to download:") % books_count
        bot.send_message(chat_id=update.message.chat_id, text=response)
        self.logger.info("Send message to user %s: %s" % (update.message.from_user.username, response))

        response = self.BookPager(books, 1, query)
        bot.send_message(chat_id=update.message.chat_id, text=response['message'], parse_mode='HTML', reply_markup=response['buttons'])

    @cmdtrans
    @CheckAuthDecorator
    def getBooksPage(self, bot, update):
        callback_query = update.callback_query
        (query,page_num) = callback_query.data.split(query_delimiter, maxsplit=1)
        if (page_num == 'current'):
            return
        try:
            page_num = int(page_num)
        except:
            page_num = 1

        books = self.BookFilter(query)
        response = self.BookPager(books, page_num, query)
        bot.edit_message_text(chat_id=callback_query.message.chat_id, message_id=callback_query.message.message_id, text=response['message'], parse_mode='HTML', reply_markup=response['buttons'])
        return

    @cmdtrans
    @CheckAuthDecorator
    def downloadBooks(self, bot, update):
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
            bot.sendMessage(chat_id=update.message.chat_id, text=response, parse_mode='HTML')
            self.logger.info("Not find download links: %s" % response)
            return

        authors = ', '.join([a['full_name'] for a in book.authors.values()])
        response = ('<b>%(title)s</b>\n%(author)s\n<b>'+_("Annotation:")+'</b>%(annotation)s\n') % {'title': book.title, 'author': authors, 'annotation':book.annotation}

        buttons = [InlineKeyboardButton(book.format.upper(), callback_data='/getfileorig%s'%book_id)]
        if not book.format in settings.NOZIP_FORMATS:
            buttons += [InlineKeyboardButton(book.format.upper()+'.ZIP', callback_data='/getfilezip%s'%book_id)]
        if (config.SOPDS_FB2TOEPUB != "") and (book.format == 'fb2'):
            buttons += [InlineKeyboardButton('EPUB', callback_data='/getfileepub%s'%book_id)]
        if (config.SOPDS_FB2TOMOBI != "") and (book.format == 'fb2'):
            buttons += [InlineKeyboardButton('MOBI', callback_data='/getfilemobi%s'%book_id)]

        markup = InlineKeyboardMarkup([buttons])
        bot.sendMessage(chat_id=update.message.chat_id, text=response, parse_mode='HTML', reply_markup=markup)
        self.logger.info("Send download buttons.")
        return

    @cmdtrans
    @CheckAuthDecorator
    def getBookFile(self, bot, update):
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
            bot.sendMessage(chat_id=callback_query.message.chat_id, text=response, parse_mode='HTML')
            self.logger.info("Not find download links: %s" % response)
            return

        filename = dl.getFileName(book)
        document = None

        if re.match(r'/getfileorig',query):
            document = dl.getFileData(book)
            #document = config.SOPDS_SITE_ROOT + reverse("opds_catalog:download",kwargs={"book_id": book.id, "zip_flag": 0})

        if re.match(r'/getfilezip',query):
            document = dl.getFileDataZip(book)
            #document = config.SOPDS_SITE_ROOT + reverse("opds_catalog:download", kwargs={"book_id": book.id, "zip_flag": 1})
            filename = filename + '.zip'

        if re.match(r'/getfileepub',query):
            document = dl.getFileDataEpub(book)
            #document = config.SOPDS_SITE_ROOT+reverse("opds_catalog:convert",kwargs={"book_id": book.id, "convert_type": "epub"}))]
            filename = filename + '.epub'

        if re.match(r'/getfilemobi',query):
            document = dl.getFileDataMobi(book)
            #document = config.SOPDS_SITE_ROOT+reverse("opds_catalog:convert",kwargs={"book_id": book.id, "convert_type": "mobi"}))]
            filename = filename + '.mobi'

        if document:
            bot.send_document(chat_id=callback_query.message.chat_id,document=document,filename=filename)
            document.close()
            self.logger.info("Send file: %s" % filename)
        else:
            response = _("There was a technical error, please contact the Bot administrator.")
            bot.sendMessage(chat_id=callback_query.message.chat_id, text=response, parse_mode='HTML')
            self.logger.info("Book get error: %s" % response)
            return

        return

    @cmdtrans
    @CheckAuthDecorator
    def botCallback(self, bot, update):
        query = update.callback_query

        if re.match(r'/getfile', query.data):
            return self.getBookFile(bot, update)
        else:
            return self.getBooksPage(bot, update)

    def start(self):
        writepid(self.pidfile)
        quit_command = 'CTRL-BREAK' if sys.platform == 'win32' else 'CONTROL-C'
        self.stdout.write("Quit the sopds_telebot with %s.\n"%quit_command)
        REQUEST_KWARGS={}
        if config.SOPDS_TELEBOT_AUTH:
            REQUEST_KWARGS['proxy_url'] = config.SOPDS_TELEBOT_PROXY
        try:
            updater = Updater(token=config.SOPDS_TELEBOT_API_TOKEN, request_kwargs=REQUEST_KWARGS)
            start_command_handler = CommandHandler('start', self.startCommand)
            getBook_handler = MessageHandler(Filters.text, self.getBooks)
            download_handler = RegexHandler('^/download\d+$',self.downloadBooks)

            updater.dispatcher.add_handler(start_command_handler)
            updater.dispatcher.add_handler(getBook_handler)
            updater.dispatcher.add_handler(download_handler)
            updater.dispatcher.add_handler(CallbackQueryHandler(self.botCallback))

            updater.start_polling(clean=True)
            updater.idle()
        except InvalidToken:
            self.stdout.write('Invalid telegram token.\nSet correct token for telegram API by command:\n python3 manage.py sopds_util setconf SOPDS_TELEBOT_API_TOKEN "<token>"')
            self.logger.error('Invalid telegram token.')

        except (KeyboardInterrupt, SystemExit):
            pass            
    
    def stop(self, pid):
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError as e:
            self.stdout.write("Error stopping sopds_telebot: %s"%str(e))
    
    def restart(self, pid):
        self.stop(pid)
        self.start()

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


    

        
 

