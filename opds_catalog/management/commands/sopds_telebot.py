import os
import signal
import sys
import logging
import re

from django.core.management.base import BaseCommand
from django.conf import settings as main_settings
from django.urls import reverse

from opds_catalog.models import Book, Author
from opds_catalog import settings, dl
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
        bot.sendMessage(chat_id=update.message.chat_id, text="Здравствуйте %s! Для поиска книги, введите ее полное наименование или часть:"%(update.message.from_user.username))
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

        books = Book.objects.filter(search_title__contains=book_name.upper()).order_by('search_title', '-docdate')
        bcount = books.count()

        response = 'По Вашему запросу ничего не найдено, попробуйте еще раз.' if bcount==0 else 'Найдено %s книг(и). Выберите нужную для скачивания.'%bcount
        bot.send_message(chat_id=update.message.chat_id, text=response)
        self.logger.info("Send message to user %s: %s" % (update.message.from_user.username,response))

        if books.count()>0:
            for b in books:
                authors = ', '.join([a['full_name'] for a in b.authors.values()])
                response='<b>%(title)s</b>\n%(author)s\n/download%(link)s\n\n'%{'title':b.title, 'author':authors,'link':b.id}
                bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')

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
                                        # url=config.SOPDS_SITE_ROOT+reverse("opds_catalog:download", kwargs={"book_id": book.id, "zip_flag": 0}))]
        if not book.format in settings.NOZIP_FORMATS:
            buttons += [InlineKeyboardButton(book.format.upper()+'.ZIP', callback_data='/getfilezip%s'%book_id)]
                                             # url=config.SOPDS_SITE_ROOT+reverse("opds_catalog:download",kwargs={"book_id": book.id, "zip_flag": 1}))]
        # if (config.SOPDS_FB2TOEPUB != "") and (book.format == 'fb2'):
        #     buttons += [InlineKeyboardButton('EPUB',
        #                                      # url=config.SOPDS_SITE_ROOT+reverse("opds_catalog:convert",kwargs={"book_id": book.id, "convert_type": "epub"}))]
        # if (config.SOPDS_FB2TOMOBI != "") and (book.format == 'fb2'):
        #     buttons += [InlineKeyboardButton('MOBI',
        #                                      # url=config.SOPDS_SITE_ROOT+reverse("opds_catalog:convert",kwargs={"book_id": book.id, "convert_type": "mobi"}))]

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
            document = dl.getFileDataZip(dl.getFileData(book), filename)
            #document = config.SOPDS_SITE_ROOT + reverse("opds_catalog:download", kwargs={"book_id": book.id, "zip_flag": 1})
            filename = filename + '.zip'

        if document:
            bot.send_document(chat_id=query.message.chat_id,document=document,filename=filename)
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


    

        
 

