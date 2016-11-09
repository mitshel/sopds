#### Simple OPDS Catalog - Простой OPDS Каталог  
#### Author: Dmitry V.Shelepnev  
#### Версия 0.33 beta

#### 1. Простая установка Simple OPDS (используем простую БД sqlite3)

1.1 Установка проекта  
Загрузить архив с проектом можно с сайта www.sopds.ru, 
либо из github.com следующей командой:

	git clone git@github.com:mitshel/sopds.git

1.2 Зависимости.  
- Требуется Python не ниже версии 3.3 (используется атрибут zlib.Decompressor.eof, введенный в версии 3.3)  
- Django 1.9 (для Python 3.3 необходимо устанавливать Django 1.8: https://code.djangoproject.com/ticket/25868)
- Pillow 2.9.0
- apscheduler 3.3.0

Для работы проекта необходимо установить указанные  зависимости: 

	yum install python3                   # команда установки для RedHad, Fedora, CentOS
	pip install -r requirements.txt       # для Python 3.4 и выше
	pip install -r requirements-p33.txt   # для Python 3.3

1.3 Настраиваем ./sopds/settings.py (настройки в конце файла)

	LANGUAGE_CODE = 'ru-RU'
	
	SOPDS_ROOT_LIB = < Путь к каталогу с книгами >
	SOPDS_AUTH = < False | True >
	SOPDS_SCAN_SHED_MIN  = '0,12'
	SOPDS_SCAN_SHED_HOUR = '0'
    
1.4 Производим инициализацию базы данных и заполнение начальными данными (жанры)

	python3 manage.py migrate
	python3 manage.py sopds_util --clear
	
1.5 Cоздаем суперпользователя

	python3 manage.py createsuperuser
	
1.6 Вручную запускаем разовое сканирование коллекции книг (Выполняется очень долго)

	python3 manage.py sopds_scanner scan --daemon

1.7 Запускаем встроенный HTTP/OPDS сервер

	python3 manage.py sopds_server start --daemon
	
Однако наилучшим способом, все же является настройка в качестве HTTP/OPDS серверов Apache или Nginx 
(точка входа ./sopds/wsgi.py)
	
1.8 Запускаем SCANNER сервер (опционально, необходим для автоматизированного периодического пересканирования коллекции)  
Перед запуском SCANNER сервера необходимо убедится, что сканирование, запущеное в п.1.6 уже завершено,
т.к. может возникнуть ситуация с запуском параллельного процесса сканирования, что может привести к ошибкам.
Примите во внимание, что в  настройках, указанных в п.1.3 задан периодический запуск сканирования 2 раза 
в день 12:00 и 0:00.

	python3 manage.py sopds_scanner start --daemon
	
1.9 Доступ к информации  
Если все предыдущие шаги выполнены успешно, то к библиотеке можно получить доступ по следующим URL:  

>     OPDS-версия: http://<Ваш сервер>:8001/opds/  
>     HTTP-версия: http://<Ваш сервер>:8001/

Следует принять во внимание, что по умолчанию в проекте используется простая БД sqlite3, которая
является одно-пользовательской. Поэтому пока не будет завершен процесс сканирования, запущенный 
ранее пунктом 1.6 попытки доступа к серверу будут завершаться ошибкой 
"A server error occurred.  Please contact the administrator."  
Для устранения указанной проблемы необходимо ипользовать многопользовательские БД, Например MYSQL.
	
#### 2. Настройка базы данных MySQL (опционально, но очень желательно для увеличения производительности).
2.1 Для работы с большим количеством книг, очень желательно не использовать sqlite, а настроить для работы БД MySQL.
MySQL по сравнению с sqlite работает гораздо быстрее, например скорость сканирования книг при использованиии MySQL
увеличится приблизительно в ПЯТЬ!!! раз.
Для этого необходимо сначала в БД MySQL создать базу данных "sopds" и пользователя с необходимыми правами,
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
            'PASSWORD' : 'sopds'
        }             
    }

    # DATABASES = {
    #    'default': {
    #        'ENGINE': 'django.db.backends.sqlite3',
    #        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    #    }         
    #}  

2.4 Далее необходимо для инициализации и заполнения вновь созданной БД заново выполнить пункты 1.4 - 1.9 данной инструкции
Однако, если Вы уже ранее запустили HTTP/OPDS сервер и SCANNER сервер, то потребуется сначала остановить их:

	python3 manage.py sopds_server stop
	python3 manage.py sopds_scanner stop

#### 3. Настройка конвертации fb2 в EPUB или MOBI (опционально, можно не настраивать)  

3.1 Конвертер fb2-to-epub http://code.google.com/p/fb2-to-epub-converter/
- во первых необходимо скачать последнюю версию конвертера fb2toepub по ссылке выше (текущая уже находится в проекте)
  к сожалению конвертер не совершенный и не все книги может конвертировать, но большинство все-таки конвертируется 
- далее, необходимо скопировать архив в папку **./convert/fb2toepub** и разархивировать 
- далее, компилируем проект командой make, в результате в папке  unix_dist появится исполняемый файл fb2toepub 
- в конфигурационном файле ./sopds/settings.py необходимо задать путь к этому конвертеру, например таким образом:  

>     SOPDS_FB2TOEPUB = os.path.join(BASE_DIR,'convert/fb2toepub/unix_dist/fb2toepub')

- В результате OPDS-клиенту будут предоставлятся ссылки на FB2-книгу в формате epub  

3.2 Конвертер fb2epub http://code.google.com/p/epub-tools/ (конвертер написан на Java, так что в вашей системе должнен быть установлен как минимум JDK 1.5)  
- также сначала скачать последнюю версию по ссылке выше (текущая уже находится в проекте)  
- скопировать jar-файл например в каталог **./convert/fb2epub** (Здесь уже лежит shell-скрипт для запуска jar-файла)  
- Соответственно прописать пути в файле конфигурации **./sopds/settings.py** к shell-скрипту fb2epub (данный конвертер работает также и в Windows) 

>     SOPDS_FB2TOEPUB = os.path.join(BASE_DIR, 'convert\\fb2epub\\fb2epub.cmd' if sys.platform =='win32' else 'convert/fb2epub/fb2epub' )

3.3 Конвертер fb2conv (конвертация в epub и mobi) http://www.the-ebook.org/forum/viewtopic.php?t=28447  
- Необходимо установить python 2.7 и пакеты lxml, cssutils:   
  
         yum install python  
         yum install python-lxml  
         yum install python-cssutils  
  
- скачать последнюю версию конвертера по ссылке выше (текущая уже находится в каталоге fb2conv проекта)  
- скачать утилиту KindleGen с сайта Amazon http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000234621 
  (текущая версия утилиты уже находится в каталоге fb2conv проекта)  
- скопировать архив проекта в **./convert/fb2conv** (Здесь уже подготовлены shell-скрипты для запуска конвертера) и разархивировать его  
- Для конвертации в MOBI нужно архив с утилитой KindleGen положить в каталог с конвертером и разархивировать  
- В конфигурационном файле **./sopds/settings.py** задать пути к соответствующим скриптам:  
   
>     SOPDS_FB2TOEPUB = os.path.join(BASE_DIR,'convert/fb2conv/fb2epub')
>     SOPDS_FB2TOMOBI = os.path.join(BASE_DIR,'convert/fb2conv/fb2mobi')

