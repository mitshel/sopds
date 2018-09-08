#### SimpleOPDS Catalog - Простой OPDS Каталог
#### Author: Dmitry V.Shelepnev  
#### Версия 0.47-devel

[English README.md](README.md)

#### 1. Простая установка SimpleOPDS (используем простую БД sqlite3)

1.1 Установка проекта  
Загрузить архив с проектом можно с сайта www.sopds.ru, 
либо из github.com следующей командой:

	git clone https://github.com/mitshel/sopds.git

1.2 Зависимости.  
- Требуется Python не ниже версии 3.4
- Django 1.10
- Pillow 2.9.0
- apscheduler 3.3.0
- django-picklefield
- lxml
- python-telegram-bot 10

Для работы проекта необходимо установить указанные  зависимости: 

	yum install python3                            # команда установки для RHEL, Fedora, CentOS
	python3 -m pip install -r requirements.txt
   
1.3 Производим инициализацию базы данных и заполнение начальными данными (жанры)

	python3 manage.py migrate
	python3 manage.py sopds_util clear
	
1.4 Cоздаем суперпользователя

	python3 manage.py createsuperuser
	
1.5 Настраиваем путь к Вашему каталогу с книгами и при необходимости переключаем язык интерфейса на русский

	python3 manage.py sopds_util setconf SOPDS_ROOT_LIB 'Путь к каталогу с книгами'
	python3 manage.py sopds_util setconf SOPDS_LANGUAGE ru-RU
		
1.6 Запускаем SCANNER сервер (опционально, необходим для автоматизированного периодического пересканирования коллекции) 
    Примите во внимание, что в  настройках по умолчанию задан периодический запуск сканирования 2 раза в день 12:00 и 0:00.

	python3 manage.py sopds_scanner start --daemon

1.7 Запускаем встроенный HTTP/OPDS сервер

	python3 manage.py sopds_server start --daemon
	
Однако наилучшим способом, все же является настройка в качестве HTTP/OPDS серверов Apache или Nginx 
(точка входа ./sopds/wsgi.py)
	
1.8 Чтобы не дожидаться начала сканирования по расписанию, можно сообщить процессу sopds_scanner о необходимости
    немедленного сканирования. Сделать это можно, установив конфигурационный параметр SOPDS_SCAN_START_DIRECTLY = True 
    двумя способами:

а) из консоли при помощи команды

	python3 manage.py sopds_util setconf SOPDS_SCAN_START_DIRECTLY True
	
б) При попомощи страницы администрирования Web-интерфейса http://<Ваш сервер>:8001/admin/ 
   (Далее CONSTANCE -> Настройки -> 1. General Options -> SOPDS_SCAN_START_DIRECTLY)
	
1.9 Доступ к информации  
Если все предыдущие шаги выполнены успешно, то к библиотеке можно получить доступ по следующим URL:  

>     OPDS-версия: http://<Ваш сервер>:8001/opds/  
>     HTTP-версия: http://<Ваш сервер>:8001/

Следует принять во внимание, что по умолчанию в проекте используется простая БД sqlite3, которая
является одно-пользовательской. Поэтому пока не будет завершен процесс сканирования, запущенный 
ранее, попытки доступа к серверу могут завершаться ошибкой
"A server error occurred.  Please contact the administrator."  
Для устранения указанной проблемы необходимо ипользовать многопользовательские БД, Например MYSQL.

1.10 При необходимости настраиваем и запускаем Telegram-бот    

Процесс создания ботов в телеграм очень прост, для создания своего бота в мессенджере Telegram необходимо подключиться к
каналу [@BotFather](https://telegram.me/botfather) и дать команду создания нового бота **/newbot**. После чего ввести имя бота 
(например: **myopds**), а затем имя пользователя для этого бота, обязательно заканчивающегося на "bot" (например: **myopds_bot**).
В результате, вам будет выдан API_TOKEN, который нужно использовать в следующих командах, которые запустят Вашего личного 
телеграм-бота, который позволит Вам, используя мессенджер Telegram получать быстрый доступ к личной библиотеке.    

    python3 manage.py sopds_util setconf SOPDS_TELEBOT_API_TOKEN  "<Telegram API Token>"
    python3 manage.py sopds_util setconf SOPDS_TELEBOT_AUTH False
    python3 manage.py sopds_telebot start --daemon
    
Командой,    

    python3 manage.py sopds_util setconf SOPDS_TELEBOT_AUTH True
    
можно ограничить использование Вашего бота пользователями Telegram. В этом случае Ваш бот будет обслуживать запросы только таких 
пользователей, чье имя в telegram совпадает с существующим имененм пользователей в вашей БД Simple OPDS.

	
#### 2. Настройка базы данных MySQL (опционально, но очень желательно для увеличения производительности).
2.1 Для работы с большим количеством книг, очень желательно не использовать sqlite, а настроить для работы БД MySQL.
MySQL по сравнению с sqlite работает гораздо быстрее. Кроме того SQLite - однопользователская БД, т.е. во время сканирования доступ
к БД будет невозможен.

 Для работы с БД Mysql в разных системах может потребоваться установка дополнительных пакетов:
   
    UBUNTU:    sudo apt-get install python3-mysqldb
    СENTOS-7:  pip3 install mysqlclient

Далее необходимо сначала в БД MySQL создать базу данных "sopds" и пользователя с необходимыми правами,
например следующим образом:

	mysql -uroot -proot_pass mysql  
	mysql > create database if not exists sopds default charset=utf8;  
	mysql > grant all on sopds.* to 'sopds'@'localhost' identified by 'sopds';  
	mysql > commit;  
	mysql > ^C  
	
2.2 Далее в конфигурационном файде нужно закомментировать строки подключения к БД sqlite и соответсвенно раскомментировать
строки подключения к БД Mysql:


	DATABASES = {
	    'default': {
	        'ENGINE': 'django.db.backends.mysql',
	        'NAME': 'sopds',
	        'HOST': 'localhost',
	        'USER': 'sopds',
	        'PASSWORD' : 'sopds',
	        'OPTIONS' : {
	            'init_command': "SET default_storage_engine=MyISAM;\
	                             SET sql_mode='';"
	        }
	    }
	}


    # DATABASES = {
    #    'default': {
    #        'ENGINE': 'django.db.backends.sqlite3',
    #        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    #    }         
    #}  

2.4 Использование InnoDB вместо MyISAM.  
Указанная выше конфигурация MySQL использует в качестве движка БД MyISAM, который работает на большинтсве версий MySQL или MariaDB.
Однако, если вы используете относительно свежие версии БД Mysql (MariaDB>=10.2.2, Mysql>=5.7.9), то у вас есть возможность использовать более современный движок InnoDB. 
Он несколько быстрее и поддерживает транзакции, что положительно скажется на целостности БД.   
(На более старых версиях MySQL с ним возникают проблемы из-за ограничений на максимальную длину индексов.)  
Таким образом, если у Вас современная версия MySQL (MariaDB>=10.2.2, Mysql>=5.7.9), то в настройках БД Mysql вместо указанных выше параметров OPTIONS просто используйте следующие:

    'OPTIONS' : {
        'init_command': """SET default_storage_engine=INNODB; \
                           SET sql_mode='STRICT_TRANS_TABLES'; \
                           SET NAMES UTF8 COLLATE utf8_general_ci; \
                           SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED
                        """
    }

2.5 Далее необходимо для инициализации и заполнения вновь созданной БД заново выполнить пункты 1.3 - 1.8 данной инструкции
Однако, если Вы уже ранее запустили HTTP/OPDS сервер и SCANNER сервер, то потребуется сначала остановить их:

	python3 manage.py sopds_server stop
	python3 manage.py sopds_scanner stop
	
#### 3. Настройка базы данных PostgreSQL (опционально, хороший вариант использования программы SimpleOPDS).
3.1 PostgreSQL - nявляется хорошим вариантом использования ПО SimpleOPDS.
Для использования PostgreSQL этого неоюбходимо установить эту БД и настроить ее (подробное описание можно найти в Интернет, напримр здесь: http://alexxkn.ru/node/42 или здесь: http://www.fight.org.ua/database/install_posqgresql_ubuntu.html):

    UBUNTU: 
    	sudo apt-get install postgresql postgresql-client postgresql-contrib libpq-dev
    	sudo vi /etc/postgresql/9.5/main/pg_hba.conf
    	sudo /etc/init.d/postgresql restart
    	
    CENTOS: 
      yum install postgresql postgresql-server
	   /usr/bin/postgresql-setup initdb
      vi /var/lib/pgsql/data/pg_hba.conf
      systemctl enable postgresql
      systemctl start postgresql
      
редактируя файл hba.conf нужно исправить следующие строки:  

    - local   all             all                                     peer
    - host    all             all             127.0.0.1/32            ident
    + local   all             all                                     md5
    + host    all             all             127.0.0.1/32            md5

    
Для работы с БД PostgreSQL скорее всего потребуется установить дополнительный пакет psycopg2:   
   
    pip3 install psycopg2

Далее необходимо сначала в БД PostgreSQL создать базу данных "sopds" и пользователя с необходимыми правами,
например следующим образом:

    psql -U postgres
	 Password for user postgres: *****
	 postgres=# create role sopds with password 'sopds' login;
	 postgres=# create database sopds with owner sopds;
	 postgres=# \q
	
3.2 Далее в конфигурационном файде нужно закомментировать строки подключения к БД sqlite и соответсвенно раскомментировать
строки подключения к БД PostgreSQL:

	 DATABASES = {
	    'default': {
	    'ENGINE': 'django.db.backends.postgresql_psycopg2',
	    'NAME': 'sopds',
	    'USER': 'sopds',
	    'PASSWORD': 'sopds',
	    'HOST': '', # Set to empty string for localhost.
	    'PORT': '', # Set to empty string for default.
	    }
	 }


     # DATABASES = {
     #    'default': {
     #        'ENGINE': 'django.db.backends.sqlite3',
     #        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
     #    }         
     #}  

3.4 Далее необходимо для инициализации и заполнения вновь созданной БД заново выполнить пункты 1.3 - 1.8 данной инструкции
Однако, если Вы уже ранее запустили HTTP/OPDS сервер и SCANNER сервер, то потребуется сначала остановить их:

	 python3 manage.py sopds_server stop
	 python3 manage.py sopds_scanner stop
	
#### 4. Настройка конвертации fb2 в EPUB или MOBI (опционально, можно не настраивать)  

4.1 Конвертер fb2-to-epub http://code.google.com/p/fb2-to-epub-converter/
- во первых необходимо скачать последнюю версию конвертера fb2toepub по ссылке выше (текущая уже находится в проекте)
  к сожалению конвертер не совершенный и не все книги может конвертировать, но большинство все-таки конвертируется 
- далее, необходимо скопировать архив в папку **./convert/fb2toepub** и разархивировать 
- далее, компилируем проект командой make, в результате в папке  unix_dist появится исполняемый файл fb2toepub 
- При помощи веб-интерфейса администратора или указанных ниже команд консоли задать путь к этому конвертеру:  

>     python3 manage.py sopds_util setconf SOPDS_FB2TOEPUB "convert/fb2toepub/unix_dist/fb2toepub"

- В результате OPDS-клиенту будут предоставлятся ссылки на FB2-книгу в формате epub  

4.2 Конвертер fb2epub http://code.google.com/p/epub-tools/ (конвертер написан на Java, так что в вашей системе должнен быть установлен как минимум JDK 1.5)  
- также сначала скачать последнюю версию по ссылке выше (текущая уже находится в проекте)  
- скопировать jar-файл например в каталог **./convert/fb2epub** (Здесь уже лежит shell-скрипт для запуска jar-файла)  
- При помощи веб-интерфейса администратора или указанных ниже команд консоли задать путь shell-скрипту fb2epub (или fb2epub.cmd для Windows) 

>     python3 manage.py sopds_util setconf SOPDS_FB2TOEPUB "convert/fb2epub/fb2epub"

4.3 Конвертер fb2conv (конвертация в epub и mobi)  
    http://www.the-ebook.org/forum/viewtopic.php?t=28447  
    https://github.com/rupor-github/fb2mobi/releases  
- Необходимо установить python 2.7 (однако для последней версии с GitHub этого делать уже не нужно, т.к. она использует как и SOPDS python3) 
  и пакеты lxml, cssutils:   
  
         yum install python  
         yum install python-lxml  
         yum install python-cssutils  
  
- скачать последнюю версию конвертера по ссылке выше (текущая уже находится в каталоге fb2conv проекта)  
- скачать утилиту KindleGen с сайта Amazon http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000234621 
  (текущая версия утилиты уже находится в каталоге fb2conv проекта)  
- скопировать архив проекта в **./convert/fb2conv** (Здесь уже подготовлены shell-скрипты для запуска конвертера) и разархивировать его  
- Для конвертации в MOBI нужно архив с утилитой KindleGen положить в каталог с конвертером и разархивировать  
- При помощи веб-интерфейса администратора или указанных ниже команд консоли задать пути к соответствующим скриптам:  
   
>     python3 manage.py sopds_util setconf SOPDS_FB2TOEPUB "convert/fb2conv/fb2epub"
>     python3 manage.py sopds_util setconf SOPDS_FB2TOMOBI "convert/fb2conv/fb2mobi"

#### 5. Консольные команды Simple OPDS  

Показать информацию о коллекции книг:  

    python3 manage.py sopds_util info
    
Очистить базу данных с коллекцией книг, загрузить справочник жанров:

    python3 manage.py sopds_util clear [--verbose]
    
Сохранить свой справочник жанров в файл opds_catalog/fixtures/mygenres.json:

    python3 manage.py sopds_util save_mygenres
    
Загрузить свой справочник жанров из файла opds_catalog/fixtures/mygenres.json:

    python3 manage.py sopds_util load_mygenres   
    
Только при использовании PostgerSQL. Оптимизация таблицы opds_catalog_book (fillfactor = 50). После этого сканирование происходит значительно быстрее:

    python3 manage.py sopds_util pg_optimize  
    
Посмотреть все параметры конфигурации:

    python3 manage.py sopds_util getconf  
    
Посмотреть значение конкретного параметра конфигурации:

    python3 manage.py sopds_util getconf SOPDS_ROOT_LIB
    
Задать значение конкретного параметр конфигурации:

    python3 manage.py sopds_util setconf SOPDS_ROOT_LIB '\home\files\books'
                 
Запустить однократное сканирование коллекции книг:

    python3 manage.py sopds_scanner scan [--verbose] [--daemon]
    
Запустить сканирование коллекции книг по расписанию:    

    python3 manage.py sopds_scanner start [--verbose] [--daemon]
   
Запустить встроенный web-сервер:    

    python3 manage.py sopds_server start [--host <IP address>] [--port <port N>] [--daemon]    


#### 6. Опции каталогизатора Simple OPDS (www.sopds.ru)
Каталогизатор Simple OPDS имеет дополнительные настройки которые можно изменять при помощи интерфейса администратора http://<Ваш сервер>/admin/  

**SOPDS_LANGUAGE** - изменение языка интерфейса. 

**SOPDS_ROOT_LIB** - содержит путь к каталогу, в котором расположена ваша коллекция книг.  

**SOPDS_BOOK_EXTENSIONS** - Список форматов книг, которые будут включаться в каталог.  
(по умолчанию SOPDS_BOOK_EXTENSIONS = '.pdf .djvu .fb2 .epub')  
	
**SOPDS_DOUBLES_HIDE** - Скрывает, найденные дубликаты в выдачах книг.  
(по умолчанию SOPDS_DOUBLES_HIDE = True)  
	
**SOPDS_FB2SAX** - Программа может извлекать метаданные из FB2 двумя парсерами 
  - FB2sax - штатный парсер, используемый в SOPDS с версии 0.01, этот парсер более быстрый, и извлекает метаданные даже из невалидных файлов FB2
  - FB2xpath - появился в версии 0.42, работает помеделеннее, не терпит невалидных FB2
(по умолчанию SOPDS_FB2SAX = True)  
	
**SOPDS_COVER_SHOW** - способ показа обложек (False - не показывать, True - извлекать обложки на лету и показывать).  
(по умолчанию SOPDS COVER_SHOW = True)  
    
**SOPDS_ZIPSCAN** - Настройка сканирования ZIP архивов.  
(по умолчанию SOPDS_ZIPSCAN = True)  
	
**SOPDS_ZIPCODEPAGE** - Указываем какая кодировка для названий файлов используется в ZIP-архивах. Доступные кодировки: cp437, cp866, cp1251, utf-8. По умолчанию применяется кодировка cp437. Поскольку в самом ZIP архиве сведения о кодировке, в которой находятся имена файлов - отсутствуют, то автоматически определить правильную кодировку для имен файлов не представляется возможным, поэтому для того чтобы кириллические имена файлов не ваыглядели как крякозябры следует применять кодировку cp866.  
(по умолчанию SOPDS_ZIPCODEPAGE = "cp866")  

**SOPDS_INPX_ENABLE** - Если True, то при обнаружении INPX файла в каталоге, сканер не сканирует его содержимое вместе с подгаталогами, а загружает	данные из найденного INPX файла. Сканер считает что сами архивыс книгами расположены в этом же каталоге. Т.е. INPX-файл должен находится именно в папке с архивами книг. 
Однако учтите, что использование данныз из INPX приведет к тому, что в библиотеке будет отсутствовать аннотация, т.к. в INPX аннотаций нет!!!  
(по умолчанию SOPDS_INPX_ENABLE = True)  

**SOPDS_INPX_SKIP_UNCHANGED** - Если True, то сканер пропускает повторное сканирование, если размер INPX не изменялся.  
(по умолчанию SOPDS_INPX_SKIP_UNCHANGED = True)  

**SOPDS_INPX_TEST_ZIP** - Если  True, то сканер пытается найти описанный в INPX архив. Если какой-то архив не обнаруживается, то сканер не будет добавлять вязанные с ним данные из INPX в базу данных соответсвенно, если SOPDS_INPX_TEST_ZIP = False, то никаких проверок сканер не производит, а просто добавляет данные из INPX в БД. Это гораздо быстрее.  
(по умолчанию SOPDS_INPX_TEST_ZIP = False)  

**SOPDS_INPX_TEST_FILES** - Если  True, то сканер пытается найти описанный в INPX конкретный файл с книгой (уже внутри архивов). Если какой-то файл не обнаруживается, то сканер не будет добавлять эту книгу в базу данных соответсвенно, если INPX_TEST_FILES = False, то никаких проверок сканер не производит, а просто добавляет книгу из INPX в БД. Это гораздо быстрее.
(по умолчанию SOPDS_TEST_FILES = False)  

**SOPDS_DELETE_LOGICAL** - True приведет к тому, что при обнаружении сканером, что книга удалена, запись в БД об этой книге будет удалена логически (avail=0). Если значение False, то произойдет физическое удаление таких записей из базы данных. Пока работает только SOPDS_DELETE_LOGICAL = False.  
(по умолчанию SOPDS_DELETE_LOGICAL = False)  

**SOPDS_SPLITITEMS** - Устанавливает при достижении какого числа элементов в группе - группа будет "раскрываться". Для выдач "By Title", "By Authors", "By Series".  
(по умолчанию SOPDS_SPLITITEMS = 300)  

**SOPDS_MAXITEMS** - Количество выдаваемых результатов на одну страницу.  
(по умолчанию SOPDS_MAXITEMS = 60)  

**SOPDS_FB2TOEPUB** и **SOPDS_FB2TOMOBI** задают пути к програмам - конвертерам из FB2 в EPUB и MOBI.
(по умолчанию SOPDS_FB2TOEPUB = "")  
(по умолчанию SOPDS_FB2TOMOBI = "")  

**SOPDS_TEMP_DIR** задает путь к временному каталогу, который используется для копирования оригинала и результата конвертации.  
(по умолчанию SOPDS_TEMP_DIR = os.path.join(BASE_DIR,'tmp'))  

**SOPDS_TITLE_AS_FILENAME** - Если True, то при скачивании вместо оригинального имени файла книги выдает транслитерацию названия книги.  
(по умолчанию SOPDS_TITLE_AS_FILENAME = True)  

**SOPDS_ALPHABET_MENU** - Включение дополнительного меню выбора алфавита.  
(по умолчанию SOPDS_ALPHABET_MENU = True)  

**SOPDS_NOCOVER_PATH** - Файл обложки, которая будет демонстрироваться для книг без обложек.  
(по умолчанию SOPDS_NOCOVER_PATH = os.path.join(BASE_DIR,'static/images/nocover.jpg'))

**SOPDS_AUTH** - Включение BASIC - авторизации.  
(по умолчанию SOPDS_AUTH = True)  

**SOPDS_SERVER_LOG** и **SOPDS_SCANNER_LOG** задают размещение LOG файлов этих процессов.  
(по умолчанию SOPDS_SERVER_LOG = os.path.join(BASE_DIR,'opds_catalog/log/sopds_server.log'))  
(по умолчанию SOPDS_SCANNER_LOG = os.path.join(BASE_DIR,'opds_catalog/log/sopds_scanner.log'))  

**SOPDS_SERVER_PID** и **SOPDS_SCANNER_PID** задают размещение PID файлов этих процессов при демонизации.  
(по умолчанию SOPDS_SERVER_PID = os.path.join(BASE_DIR,'opds_catalog/tmp/sopds_server.pid'))  
(по умолчанию SOPDS_SCANNER_PID = os.path.join(BASE_DIR,'opds_catalog/tmp/sopds_scanner.pid'))  

Параметры **SOPDS_SCAN_SHED_XXX** устанавливают значения шедулера, для периодического сканирования коллекции книг при помощи **manage.py sopds_scanner start**.  Возможные значения можно найти на следующей странице: # https://apscheduler.readthedocs.io/en/latest/modules/triggers/cron.html#module-apscheduler.triggers.cron  
Изменения указанных ниже параметров через Web-интерфейс или командную строку проверяется процессом sopds_scanner каждые 10 минут. 
В случае обнаружения изменений sopds_scanner автоматически вносит соответсвующие изменения в планировщик.  

(по умолчанию SOPDS_SCAN_SHED_MIN = '0')  
(по умолчанию SOPDS_SCAN_SHED_HOUR = '0,12')  
(по умолчанию SOPDS_SCAN_SHED_DAY = '*')  
(по умолчанию SOPDS_SCAN_SHED_DOW = '*')  

**SOPDS_SCAN_START_DIRECTLY** - установка для этого параметра значения True, приведет к тому, что при очередной проверке процессом sopds_scanner этого флага (каждые 10 минут)
запустится внеочередное сканированеи коллекции, а указаный флаг вновь сброситься в False.

**SOPDS_CACHE_TIME** - Время хранения страницы в кэше
(по умолчанию SOPDS_CACHE_TIME = 1200)

**SOPDS_TELEBOT_API_TOKEN** - API TOKEN для Telegram Бота
**SOPDS_TELEBOT_AUTH** - Если True, то Бот будет предоставлять доступ к библиотеке, только пользователям, чье имя в Telegram совпадает с именем
существующего пользователя в БД Simple OPDS.
(по умолчанию SOPDS_TELEBOT_AUTH = True)

**SOPDS_TELEBOT_MAXITEMS** - Максимальное число одновременно выводимых элеменов в сообщении Telegram
(по умолчанию SOPDS_TELEBOT_MAXITEMS = 10)