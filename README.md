#### SimpleOPDS Catalog
#### Author: Dmitry V.Shelepnev
#### Version 0.47-devel

[Инструкция на русском языке: README_RUS.md](README_RUS.md)

#### 1. Simple installation of SimpleOPDS (by using sqlite3 database)

1.1 Installing the project
You can download the archive with the project from www.sopds.ru,
or from github.com with the following command:

	git clone https://github.com/mitshel/sopds.git

1.2 Dependencies.
- Requires Python at least version 3.4
- Django 1.10
- Pillow 2.9.0
- apscheduler 3.3.0
- django-picklefield
- lxml
- python-telegram-bot 10

The following dependencies should be established for the project:

    yum install python3                            # setup command for RHEL, Fedora, CentOS
    python3 -m pip install -r requirements.txt

1.3 We initialize the database and fill in the initial data (genres)

	python3 manage.py migrate
	python3 manage.py sopds_util clear

1.4 Creating a Superuser

	python3 manage.py createsuperuser

1.5 We adjust the path to your catalog with books and, if necessary, switch the interface language to English

	python3 manage.py sopds_util setconf SOPDS_ROOT_LIB 'Path to the directory with books'
	python3 manage.py sopds_util setconf SOPDS_LANGUAGE en-EN

1.6 Launch the SCANNER server (optional, required for automated periodic re-scanning of the collection)
    Please note that the default settings specify a periodic scan start 2 times a day 12:00 and 0:00.

	python3 manage.py sopds_scanner start --daemon

1.7 Starting the built-in HTTP / OPDS server

	python3 manage.py sopds_server start --daemon

However, the best way is still to configure the HTTP / OPDS servers as Apache or Nginx
(entry point ./sopds/wsgi.py)

1.8 In order not to wait for the start of a scheduled scan, you can tell the sopds_scanner process about the need immediate scanning. You can do this by setting the configuration parameter SOPDS_SCAN_START_DIRECTLY = True two ways:

a) from the console using the command

	python3 manage.py sopds_util setconf SOPDS_SCAN_START_DIRECTLY True

b) With the help of the Web-interface administration page http://<Your server>:8001/admin/
   (FCONSTANCE -> Settings -> 1. General Options -> SOPDS_SCAN_START_DIRECTLY)

1.9 Access to information
If all previous steps were successful, then the library can be accessed by the following URLs:

>     OPDS-version: http://<Your server>:8001/opds/
>     HTTP-version: http://<Your server>:8001/

It should be taken into account that by default the project uses a simple sqlite3 database, which
is one-user. Therefore, until the scanning process is completed, the attempts to access the server may result in an error
"A server error occurred." Please contact the administrator. "
To eliminate this problem, you need to use multi-user databases, for example MYSQL.

1.10 If necessary, configure and run Telegram-bot

The process of creating bots in telegrams is very simple, to create your bot in Telegram, you need to connect to
channel [@BotFather] (https://telegram.me/botfather) and give the command to create a new bot **/newbot**. Then enter the name of the bot
(for example: **myopds**), and then the user name for this bot, which necessarily ends with "bot" (for example: **myopds_bot**).
As a result, you will be given API_TOKEN, which you need to use in the following commands that will start your personal
telegram-bot, which will allow you, using the Telegram instant messenger to get quick access to your personal library.

    python3 manage.py sopds_util setconf SOPDS_TELEBOT_API_TOKEN "<Telegram API Token>"
    python3 manage.py sopds_util setconf SOPDS_TELEBOT_AUTH False
    python3 manage.py sopds_telebot start --daemon
    
Team,

    python3 manage.py sopds_util setconf SOPDS_TELEBOT_AUTH True
    
you can limit the use of your bot by Telegram users. In this case, your bot will serve only those
users whose name in the telegram matches the existing user name in your Simple OPDS database.

#### 2. Configuring the MySQL database (optional, but very desirable for increasing performance).
2.1 To work with a large number of books, it is highly advisable not to use sqlite, but to configure MySQL databases to work. MySQL is much faster than sqlite. In addition, SQLite is a single-user database, i.e. during scanning access to a DB it will be impossible.

 To work with the Mysql database on different systems, you may need to install additional packages:

    UBUNTU: sudo apt-get install python3-mysqldb
    CENTOS-7: pip3 install mysqlclient

Next, you must first create a database "sopds" and a user with the necessary rights in the MySQL database,
for example, as follows:

	mysql -uroot -proot_pass mysql
	mysql> create database if not exists sopds default charset = utf8;
	mysql> grant all on sopds. * to 'sopds' @ 'localhost' identified by 'sopds';
	mysql> commit;
	mysql> ^ C

2.2 Then, in the configuration file, you need to comment out the connection strings to the sqlite database and uncomment the connection string to the Mysql database:


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


2.4 Using InnoDB instead of MyISAM.
The above MySQL configuration uses MyISAM as the database engine, which works on most versions of MySQL or MariaDB. However, if you use a relatively new version of Mysql (MariaDB> = 10.2.2, Mysql> = 5.7.9), then you can use the more modern InnoDB engine. It is somewhat faster and supports transactions, which will positively affect the integrity of the database. (On older versions of MySQL, there are problems with it because of restrictions on the maximum length of indexes.) Thus, if you have a modern version of MySQL (MariaDB> = 10.2.2, Mysql> = 5.7.9), then in the Mysql database settings, simply use the following instead of the above OPTIONS parameters:

    'OPTIONS' : {
        'init_command': """SET default_storage_engine=INNODB; \
                           SET sql_mode='STRICT_TRANS_TABLES'; \
                           SET NAMES UTF8 COLLATE utf8_general_ci; \
                           SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED
                        """
    }

2.5 Further it is necessary to re-execute points 1.3 - 1.8 of this instruction in order to initialize and fill the newly created database However, if you have already started the HTTP/OPDS server and the SCANNER server, you must first stop them:

	python3 manage.py sopds_server stop
	python3 manage.py sopds_scanner stop

#### 3. Configuring the PostgreSQL database (optional, a good option for using the SimpleOPDS program).
3.1 PostgreSQL is a good way to use SimpleOPDS.
To use PostgreSQL, it is necessary to install this database and configure it (for a detailed description, see the Internet, for example: http://alexxkn.ru/node/42 or here: http://www.fight.org.ua/database/ install_posqgresql_ubuntu.html):


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

editing the hba.conf file, you need to fix the following lines:

    - local   all             all                                     peer
    - host    all             all             127.0.0.1/32            ident
    + local   all             all                                     md5
    + host    all             all             127.0.0.1/32            md5


To work with the PostgreSQL database, you probably need to install an additional package of psycopg2:

    pip3 install psycopg2

Next, you must first create a database "sopds" and a user with the necessary rights in the PostgreSQL database, for example, as follows:

    psql -U postgres
	 Password for user postgres: *****
	 postgres=# create role sopds with password 'sopds' login;
	 postgres=# create database sopds with owner sopds;
	 postgres=# \q

3.2 Next in the configuration file, you need to comment out the connection strings to the sqlite database and decompress it accordingly the connection string to the PostgreSQL database:

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

3.4 Next, it is necessary to re-execute points 1.3 - 1.8 of this instruction in order to initialize and fill the newly created database However, if you have already started the HTTP/OPDS server and the SCANNER server, you must first stop them:

	 python3 manage.py sopds_server stop
	 python3 manage.py sopds_scanner stop

#### 4. Setting the conversion of fb2 to EPUB or MOBI (optionally, you can not configure it)

4.1 fb2-to-epub converter http://code.google.com/p/fb2-to-epub-converter/
- First you need to download the latest version of the fb2toepub converter from the link above (the current one is already in the project) unfortunately the converter is not perfect and not all books can be converted, but most still converted
- Further, you need to copy the archive to the folder **./convert/fb2toepub** and unzip
- Next, we compile the project with the make command, as a result, the executable file fb2toepub appears in the unix_dist folder
- Use the web interface of the administrator or the following console commands to specify the path to this converter:

>     python3 manage.py sopds_util setconf SOPDS_FB2TOEPUB "convert/fb2toepub/unix_dist/fb2toepub"

- As a result, the OPDS client will be provided with links to the FB2-book in the epub format

4.2 fb2epub converter http://code.google.com/p/epub-tools/ (the converter is written in Java, so at least JDK 1.5 should be installed on your system)
- also first download the latest version from the link above (the current one is already in the project)
- copy the jar-file to the directory **./convert/fb2epub** (There is already a shell script to run the jar-file)
- Set the path to the shell script fb2epub (or fb2epub.cmd for Windows) using the web administrator interface or the following console commands:

>     python3 manage.py sopds_util setconf SOPDS_FB2TOEPUB "convert/fb2epub/fb2epub"

4.3 Converter fb2conv (converting to epub and mobi)   
    http://www.the-ebook.org/forum/viewtopic.php?t=28447  
    https://github.com/rupor-github/fb2mobi/releases  
- It is necessary to install python 2.7 (however, for the latest version with GitHub, you do not need to do this, since it uses the same as SOPDS python3)
  and the packages lxml, cssutils:

         yum install python
         yum install python-lxml
         yum install python-cssutils

- download the latest version of the converter from the link above (the current one is already in the fb2conv directory of the project)
- download the KindleGen utility from the Amazon website http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000234621 (the current version of the utility is already in the fb2conv directory of the project)
- copy the project archive to **./convert/fb2conv** (There are already shell scripts for starting the converter) and unzip it
- To convert to MOBI you need to archive the KindleGen utility in the directory with the converter and unzip it
- Use the web-based administrator interface or the following console commands to specify paths to the corresponding scripts:

>     python3 manage.py sopds_util setconf SOPDS_FB2TOEPUB "convert/fb2conv/fb2epub"
>     python3 manage.py sopds_util setconf SOPDS_FB2TOMOBI "convert/fb2conv/fb2mobi"

#### 5. Console commands Simple OPDS

Show information about the book collection:

    python3 manage.py sopds_util info

Clear the database with a collection of books, download the genre directory:

    python3 manage.py sopds_util clear [--verbose]

Keep your genre directory in the file opds_catalog / fixtures / mygenres.json:

    python3 manage.py sopds_util save_mygenres

Download your genre directory from the opds_catalog/fixtures/mygenres.json file:

    python3 manage.py sopds_util load_mygenres

Only when using PostgerSQL. Optimization of the table opds_catalog_book (fillfactor = 50). After that, scanning is much faster:

    python3 manage.py sopds_util pg_optimize

View all configuration options:

    python3 manage.py sopds_util getconf

View the value of a specific configuration parameter:

    python3 manage.py sopds_util getconf SOPDS_ROOT_LIB

Set the value of a specific configuration parameter:

    python3 manage.py sopds_util setconf SOPDS_ROOT_LIB '\home\files\books'

Start a one-time scan of the book collection:

    python3 manage.py sopds_scanner scan [--verbose] [--daemon]

Run the scan of the collection of books on a schedule:

    python3 manage.py sopds_scanner start [--verbose] [--daemon]

Run the embedded web server:

    python3 manage.py sopds_server start [--host <IP address>] [--port <port N>] [--daemon]


#### 6. Options of the cataloger Simple OPDS (www.sopds.ru)  
The Simple OPDS cataloger has additional settings that can be changed using the admin interface http://<Your server>/admin/  

**SOPDS_LANGUAGE** - change the interface language.  

**SOPDS_ROOT_LIB** - contains the path to the directory where your book collection is located.  

**SOPDS_BOOK_EXTENSIONS** - List of book formats that will be included in the catalog.  
(by default SOPDS_BOOK_EXTENSIONS = '.pdf .djvu .fb2 .epub')  

**SOPDS_DOUBLES_HIDE** - Hides found duplicates in book issues.  
(by default SOPDS_DOUBLES_HIDE = True)  

**SOPDS_FB2SAX** - The program can extract metadata from FB2 by two parsers
  - FB2sax is the regular parser used in SOPDS from version 0.01, this parser is faster, and retrieves metadata even from invalid FB2 files  
  - FB2xpath - appeared in version 0.42, works less often, does not tolerate invalid FB2  
(by default SOPDS_FB2SAX = True)  

**SOPDS_COVER_SHOW** - a way to show skins (False - do not show, True - extract covers on the fly and show).  
(by default SOPDS COVER_SHOW = True)  

**SOPDS_ZIPSCAN** - Configures the scanning of ZIP archives.  
(by default SOPDS_ZIPSCAN = True)  

**SOPDS_ZIPCODEPAGE** - Specify which encoding for file names is used in ZIP archives. Available encodings: cp437, cp866, cp1251, utf-8. The default encoding is cp437. Since there is no information about the encoding in which the file names are located in the ZIP archive, it is not possible to automatically determine the correct encoding for filenames, so cyrillic encodings should use cp866 encoding in order for Cyrillic file names to not look like croaks.  
(default is SOPDS_ZIPCODEPAGE = "cp866")  

**SOPDS_INPX_ENABLE** - If True, if an INPX file is found in the directory, the scanner does not scan its contents with the sub-htag, but loads the data from the found INPX file. The scanner believes that the archives of books themselves are located in the same directory. Those. INPX-file should be located in the folder with the archives of books.
However, please note that using data from INPX will result in the absence of annotation in the library. INPX annotations are not present !!!  
(by default SOPDS_INPX_ENABLE = True)  

**SOPDS_INPX_SKIP_UNCHANGED** - If True, the scanner skips re-scanning if the size of INPX has not changed.  
(by default SOPDS_INPX_SKIP_UNCHANGED = True)  

**SOPDS_INPX_TEST_ZIP** - If True, the scanner tries to find the archive described in the INPX. If an archive is not found, the scanner will not add the data from INPX connected to it to the database, if SOPDS_INPX_TEST_ZIP = False, then the scanner does not perform any checks, but simply adds data from INPX to the database. It's much faster.  
(by default SOPDS_INPX_TEST_ZIP = False)  

**SOPDS_INPX_TEST_FILES** - If True, the scanner tries to find the specific file with the book described in INPX (already inside the archives). If a file is not found, the scanner will not add this book to the database, if INPX_TEST_FILES = False, then the scanner does not perform any checks, but simply adds a book from INPX to the database. It's much faster.  
(by default SOPDS_TEST_FILES = False)  

**SOPDS_DELETE_LOGICAL** - True will result in the fact that if the scanner detects that the book has been deleted, the entry in the database about this book will be deleted logically (avail = 0). If the value is False, then there will be a physical deletion of such records from the database. So far only SOPDS_DELETE_LOGICAL = False.  
(by default SOPDS_DELETE_LOGICAL = False)  

**SOPDS_SPLITITEMS** - Sets when the number of elements in the group is reached - the group will "expand". For issuing "By Title", "By Authors", "By Series".  
(the default is SOPDS_SPLITITEMS = 300)  

**SOPDS_MAXITEMS** - The number of results to be displayed per page.  
(the default is SOPDS_MAXITEMS = 60)  

**SOPDS_FB2TOEPUB** and **SOPDS_FB2TOMOBI** set the paths to the programs - converters from FB2 to EPUB and MOBI.  
(by default SOPDS_FB2TOEPUB = "")  
(by default SOPDS_FB2TOMOBI = "")  

**SOPDS_TEMP_DIR** specifies the path to the temporary directory, which is used to copy the original and the conversion result.  
(by default SOPDS_TEMP_DIR = os.path.join (BASE_DIR, 'tmp'))  

**SOPDS_TITLE_AS_FILENAME** - If True, when downloading instead of the original file name, the book will produce a transliteration of the title of the book.  
(by default SOPDS_TITLE_AS_FILENAME = True)  

**SOPDS_ALPHABET_MENU** - Includes an additional menu for selecting the alphabet.  
(by default SOPDS_ALPHABET_MENU = True)  

**SOPDS_NOCOVER_PATH** - A cover file that will be displayed for books without covers.  
(by default SOPDS_NOCOVER_PATH = os.path.join (BASE_DIR, 'static/images/nocover.jpg'))  

**SOPDS_AUTH** - Enable BASIC - authorization.  
(by default SOPDS_AUTH = True)  

**SOPDS_SERVER_LOG** and **SOPDS_SCANNER_LOG** specify the location of LOG files of these processes.  
(by default SOPDS_SERVER_LOG = os.path.join (BASE_DIR, 'opds_catalog/log/sopds_server.log'))  
(by default SOPDS_SCANNER_LOG = os.path.join (BASE_DIR, 'opds_catalog/log/sopds_scanner.log'))  

**SOPDS_SERVER_PID** and **SOPDS_SCANNER_PID** specify the location of the PID files of these processes during demonization.  
(by default SOPDS_SERVER_PID = os.path.join (BASE_DIR, 'opds_catalog/tmp/sopds_server.pid'))  
(by default SOPDS_SCANNER_PID = os.path.join (BASE_DIR, 'opds_catalog/tmp/ sopds_scanner.pid'))  

Parameters **SOPDS_SCAN_SHED_XXX** set the values ​​of the template, to periodically scan the collection of books using ** manage.py sopds_scanner start **. Possible values ​​can be found on the following page: # https://apscheduler.readthedocs.io/en/latest/modules/triggers/cron.html#module-apscheduler.triggers.cron  
Changes to the following parameters via the Web interface or the command line are checked by the sopds_scanner process every 10 minutes.  
In case of detection of changes, sopds_scanner automatically makes the appropriate changes to the scheduler.  

(default is SOPDS_SCAN_SHED_MIN = '0')  
(the default is SOPDS_SCAN_SHED_HOUR = '0,12')  
(default is SOPDS_SCAN_SHED_DAY = '*')  
(default is SOPDS_SCAN_SHED_DOW = '*')  

**SOPDS_SCAN_START_DIRECTLY** - setting this parameter to True will cause the next check of the sopds_scanner flag (every 10 minutes)  
an extraordinary scan of the collection will be launched, and the specified flag will again be reset to False.  

**SOPDS_CACHE_TIME** - Pages cache time
(default is SOPDS_CACHE_TIME = 1200)

**SOPDS_TELEBOT_API_TOKEN** - API TOKEN for Telegram Bot

**SOPDS_TELEBOT_AUTH** - If True, the Bot will grant access to the library, only to users whose name in the Telegram matches the name
existing user in the Simple OPDS database.
(by default SOPDS_TELEBOT_AUTH = True)

**SOPDS_TELEBOT_MAXITEMS** - The maximum number of simultaneously displayed items in the Telegram message
(by default SOPDS_TELEBOT_MAXITEMS = 10)
