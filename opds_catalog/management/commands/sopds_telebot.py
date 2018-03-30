import os
import signal
import sys
import logging
import re

from django.core.management.base import BaseCommand
from django.conf import settings as main_settings
from django.utils.html import strip_tags
from django.db.models import Q
from django.urls import reverse

from opds_catalog.models import Book, Author
from opds_catalog import settings, dl
from opds_catalog.opds_paginator import Paginator as OPDS_Paginator
from sopds_web_backend.settings import HALF_PAGES_LINKS
from constance import config
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Document



class Command(BaseCommand):
    help = 'SimpleOPDS Telegram Bot engine.'

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

    def startCommand(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id, text="%s\nЗдравствуйте %s! Для поиска книги, введите часть ее наименования или автора:"%
                                                             (settings.SUBTITLE,update.message.from_user.username))
        self.logger.info("Start talking with user: %s"%update.message.from_user)

    def getBooks(self, bot, update):
        book_name=update.message.text
        self.logger.info("Got message from user %s: %s" % (update.message.from_user.username, book_name))

        if len(book_name)<3:
            response = 'Слишком короткая строка для поиска, попробуйте еще раз.'
        else:
            response = 'Выполняю поиск книги: %s' % (book_name)

        bot.send_message(chat_id=update.message.chat_id, text=response)
        self.logger.info("Send message to user %s: %s" % (update.message.from_user.username,response))

        if len(book_name) < 3:
            return

        q_objects = Q()
        q_objects.add(Q(search_title__contains=book_name.upper()), Q.OR)
        q_objects.add( Q(authors__search_full_name__contains=book_name.upper()), Q.OR)

        books = Book.objects.filter(q_objects).order_by('search_title', '-docdate').distinct()
        books_count = books.count()

        if books_count == 0:
            response = 'По Вашему запросу ничего не найдено, попробуйте еще раз.'
            bot.send_message(chat_id=update.message.chat_id, text=response)
            self.logger.info("Send message to user %s: %s" % (update.message.from_user.username,response))
            return

        response = 'Найдено %s книг(и). \nФормирую список, через несколько секунд выберите нужную для скачивания:' % books_count
        bot.send_message(chat_id=update.message.chat_id, text=response)
        self.logger.info("Send message to user %s: %s" % (update.message.from_user.username, response))

        page_num = 1
        #op = OPDS_Paginator(books_count, 0, page_num, config.SOPDS_MAXITEMS, HALF_PAGES_LINKS)
        op = OPDS_Paginator(books_count, 0, page_num, 5, HALF_PAGES_LINKS)
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
                if books[finish].title.upper() == prev_title.upper() and {a['id'] for a in books[
                    finish].authors.values()} == prev_authors_set:
                    items[-1]['doubles'] += 1
                else:
                    double_flag = False

            if op.d1_first_pos != 0:
                items.pop(0)

        response = ''
        for b in items:
            authors = ', '.join([a['full_name'] for a in b['authors']])
            response+='<b>%(title)s</b>\n%(author)s\n/download%(link)s\n\n'%{'title':b['title'], 'author':authors,'link':b['id']}

        buttons = [InlineKeyboardButton('1 <<', callback_data='/p1'),
                   InlineKeyboardButton('%s <'%op.previous_page_number , callback_data='/p%s'%op.previous_page_number),
                   InlineKeyboardButton('[ %s ]'%op.number , callback_data='/p%s'%op.number),
                   InlineKeyboardButton('> %s'%op.next_page_number , callback_data='/p%s'%op.next_page_number),
                   InlineKeyboardButton('>> %s'%op.num_pages, callback_data='/p%s'%op.num_pages)]

        markup = InlineKeyboardMarkup([buttons]) if op.num_pages>1 else None

        bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML', reply_markup=markup)

    def downloadBooks(self, bot, update):
        book_id_set=re.findall(r'\d+$',update.message.text)
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
            response = 'Книга по указанной Вами ссылке не найдена, попробуйте повторить поиск книги сначала.'
            bot.sendMessage(chat_id=update.message.chat_id, text=response, parse_mode='HTML')
            self.logger.info("Not find download links: %s" % response)
            return

        authors = ', '.join([a['full_name'] for a in book.authors.values()])
        response = '<b>%(title)s</b>\n%(author)s\n<b>Аннотация:</b>%(annotation)s\n' % {'title': book.title, 'author': authors, 'annotation':book.annotation}

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

    def getBookFile(self, bot, update, user_data):
        query = update.callback_query
        book_id_set=re.findall(r'\d+$',query.data)
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
            response = 'Книга по указанной Вами ссылке не найдена, попробуйте повторить поиск книги сначала.'
            bot.sendMessage(chat_id=query.message.chat_id, text=response, parse_mode='HTML')
            self.logger.info("Not find download links: %s" % response)
            return

        filename = dl.getFileName(book)
        document = None

        if re.match(r'/getfileorig',query.data):
            document = dl.getFileData(book)
            #document = config.SOPDS_SITE_ROOT + reverse("opds_catalog:download",kwargs={"book_id": book.id, "zip_flag": 0})

        if re.match(r'/getfilezip',query.data):
            document = dl.getFileDataZip(book)
            #document = config.SOPDS_SITE_ROOT + reverse("opds_catalog:download", kwargs={"book_id": book.id, "zip_flag": 1})
            filename = filename + '.zip'

        if re.match(r'/getfileepub',query.data):
            document = dl.getFileDataEpub(book)
            #document = config.SOPDS_SITE_ROOT+reverse("opds_catalog:convert",kwargs={"book_id": book.id, "convert_type": "epub"}))]
            filename = filename + '.epub'

        if re.match(r'/getfilemobi',query.data):
            document = dl.getFileDataMobi(book)
            #document = config.SOPDS_SITE_ROOT+reverse("opds_catalog:convert",kwargs={"book_id": book.id, "convert_type": "mobi"}))]
            filename = filename + '.mobi'

        if document:
            bot.send_document(chat_id=query.message.chat_id,document=document,filename=filename)
            document.close()
            self.logger.info("Send file: %s" % filename)
        else:
            response = 'Возникла техническая ошибка, обратитесь к администратору сайта.'
            bot.sendMessage(chat_id=query.message.chat_id, text=response, parse_mode='HTML')
            self.logger.info("Book get error: %s" % response)
            return

        user_data['type'] = query.data;

        return

    def start(self):
        writepid(self.pidfile)
        quit_command = 'CTRL-BREAK' if sys.platform == 'win32' else 'CONTROL-C'
        self.stdout.write("Quit the sopds_telebot with %s.\n"%quit_command)
        try:
            updater = Updater(token=config.SOPDS_TELEBOT_API_TOKEN)

            start_command_handler = CommandHandler('start', self.startCommand)
            getBook_handler = MessageHandler(Filters.text, self.getBooks)
            download_handler = RegexHandler('^/download\d+$',self.downloadBooks)

            updater.dispatcher.add_handler(start_command_handler)
            updater.dispatcher.add_handler(getBook_handler)
            updater.dispatcher.add_handler(download_handler)
            updater.dispatcher.add_handler(CallbackQueryHandler(self.getBookFile, pass_user_data=True))

            updater.start_polling(clean=True)
            updater.idle()
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


    

        
 

