import os
import signal
import sys
import logging

from django.core.management.base import BaseCommand
from django.db import transaction, connection, connections
from django.conf import settings as main_settings

from opds_catalog.models import Book, Author, Series, bookshelf, Counter, Catalog, Genre, lang_menu
from opds_catalog import settings 
from constance import config
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

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

    def textMessage(self, bot, update):
        book_name=update.message.text
        response = 'Выполняю поиск книги: %s' % (book_name)
        self.logger.info("Got message from user %s: %s" % (update.message.from_user.username, book_name))
        bot.send_message(chat_id=update.message.chat_id, text=response)
        self.logger.info("Send message to user %s: %s" % (update.message.from_user.username,response))
        books = Book.objects.filter(search_title__contains=book_name.upper()).order_by('search_title', '-docdate')
        response = "Найдено %s книг. Выберите нужную для скачивания."%books.count()
        bot.send_message(chat_id=update.message.chat_id, text=response)
        self.logger.info("Send message to user %s: %s" % (update.message.from_user.username,response))
        if books.count()>0:
            for b in books:
                bot.send_message(chat_id=update.message.chat_id, text=b.title)
                # bot.send_message(chat_id=update.message.chat_id, text=(', '.join(a['full_name']) for a in b.authors.values()) )
                bot.send_message(chat_id=update.message.chat_id, text="Скачать книгу: %s\n\n"%b.filename)

    def start(self):
        writepid(self.pidfile)
        quit_command = 'CTRL-BREAK' if sys.platform == 'win32' else 'CONTROL-C'
        self.stdout.write("Quit the sopds_telebot with %s.\n"%quit_command)
        try:
            updater = Updater(token=config.SOPDS_TELEBOT_API_TOKEN)

            start_command_handler = CommandHandler('start', self.startCommand)
            text_message_handler = MessageHandler(Filters.text, self.textMessage)

            updater.dispatcher.add_handler(start_command_handler)
            updater.dispatcher.add_handler(text_message_handler)
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


    

        
 

