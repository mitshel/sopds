Simple OPDS Catalog
Простой OPDS Каталог
Author: Dmitry V.Shelepnev
Версия 0.17

Установка Simple OPDS в Fedora:

1. Зависимости.
Требуется Mysql не ниже версии 5 (необходима поддержка хранимых процедур)
Требуется Python не ниже версии 3.3 (используется атрибут zlib.Decompressor.eof, введенный в версии 3.3)

Для работы проекта необходимо установить следующие зависимости:
yum install httpd
yum install mysql
yum install python3
yum install mysql-connector-python3

2. Установка.
Загрузить проект можно с сайта www.sopds.ru. 
Проект имеет следующую структуру:
opds				- каталог проекта (можно задать свое имя каталога)
	py			- каталог с программами на Python
	db			- каталог инициализационные скрипты для создания БД
	conf			- каталог с файлом конфигурации
	README.md		- файл README

Для работы CGI-скрипта необходимо разрешить доступ к каталогу opds, например при помощи следующих директив конфигурационного файла web-сервера Apache httpd.conf:

<Directory "/home/www/opds">
        Options Indexes FollowSymLinks
        AllowOverride All
        Order allow,deny
        Allow from all
</Directory>
Alias   /opds           "/home/www/opds"

3. Конфигурационный файл.
Перед началом работы необходимо внести необходимые настройки в файл конфигурации ./conf/sopds.conf

4. Инициализация базы данных.
Во первых для работы каталога необходимо создать базу данных "sopds" и пользователя с необходимыми правами, например
следующим образом:
  mysql -uroot -proot_pass mysql
  mysql > create database if not exists sopds default charset=utf8;
  mysql > grant select,insert,update,delete,execute on sopds.* to 'sopds'@'localhost' identified by 'sopds';
  mysql > commit;
  mysql > ^C

Далее в созданную базу данных необходимо загрузить структуру БД и заполненную таблицу жанров, например
следующим образом:
  mysql -uroot -proot_pass sopds < ./db/tables.sql
  mysql -uroot -proot_pass sopds < ./db/genres.sql

Все указанные выше процедуры могут быть выполнены при помощи скрипта ./db/db_create.sh суперпользователем root (для Fedora)

5. Сканирование каталога с книгами.
Для однократого сканирования каталога с электронными книгами можно запустить скрипт sopds-scan.py
Для запуска периодического сканирования согласно настроек секции [daemon] конфигурационого файла необходимо запустить сканнер книг
в режиме демона командой ./sopdsd.py start

6. Доступ к OPDS каталогу через WWW.

6.1 Использование CGI
Для сервера Apache необходимо разрешить запуск cgi-скрипта ./py/sopds.cgi
при помощи директивы, помещенной в .htacess:
  Options ExecCGI
или
  Options +ExecCGI

6.2 Использование WSGI
Для начала необходимо установить mod_wsgi в Apache
Далее необходимо разрешить запуск wsgi-скрипта ./py/sopds.wsgi
при помощи директив, помещенной в .htacess:
  AddHandler wsgi-script .wsgi
  Options ExecCGI
или
  AddHandler wsgi-script .wsgi
  Options +ExecCGI

Описания по нектороым проблемам, которые могут возникнуть с mod_wsgi: https://code.google.com/p/modwsgi/wiki/IssuesWithExpatLibrary

7. Использование OPDS каталога с устройств поддерживающих OPDS.
Ввести OPDS каталог и следующий URL: your_domain_name/opds/py/sopds.cgi
Либо, если Вы используете WSGI     : your_domain_name/opds/py/sopds.wsgi

8. Обновление версий
- Поскольку при переходе от версии к версии возможно изменение структуры БД необходимо пересоздать ее следующей командой
  ./db/db_create.sh либо выполнить рекомендации в п.4
- После пересоздания БД и, как следствие уничтожении сыллок из БД на извлеченные обложки стоит удалить со всем содержимым
  папку covers
  rm -rf covers

9. Настройка конвертации fb2 в EPUB или MOBI (возможно кому-нибудь нужно)
   9.1 - Конвертер fb2-to-epub http://code.google.com/p/fb2-to-epub-converter/
   - во первых необходимо скачать последнюю версию конвертера fb2toepub по ссылке выше (текущая уже находится в проекте)
     к сожалению конвертер не совершенный и не все книги может конвертирвать, но большинство все-таки конвертируется
   - далее, необходимо скопировать архив в папку opds/fb2toepub и разархивировать 
   - далее, компилируем проект командой make, в результате в папке  unix_dist появится исполняемый файл fb2toepub
   - в конфигурационном файле sopds.conf необходимо задать путь к этому конвертеру, а также путь к временной папке, куда будут помещаться сконвертированные файлы,
     например таким образом:
     fb2toepub=../fb2toepub/unix_dist/fb2toepub
     temp_dir=/tmp
   - В результате OPDS-клиенту будут предоставлятся ссылки на FB2-книгу в формате epub

   9.2 - Конвертер fb2epub http://code.google.com/p/epub-tools/ (конвертер написан на Java, так что в вашей системе должнен быть установлен как минимум JDK 1.5)
   - также сначала скачать последнюю версию по ссылке выше (текущая уже находится в проекте)
   - скопировать jar-файл например в каталог opds/fb2epub (Здесь уже лежит shell-скрипт для запуска jar-файла)
   - Соответственно прописать пути в файле конфигурации sopds.conf к shell-скрипту fb2epub
     fb2toepub=../fb2epub/fb2epub
     temp_dir=/tmp

   9.3 - Конвертер fb2conv (конвертация в epub и mobi) http://www.the-ebook.org/forum/viewtopic.php?t=28447
   - Необходимо установить python 2.7 и пакеты lxml, cssutils:
     yum install python
     yum install python-lxml
     yum install python-cssutils
   - скачать последнюю версию конвертера по ссылке выше (текущая уже находится в каталоге fb2conv проекта)
   - скачать утилиту KindleGen с сайта Amazon http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000234621 (текущая версия утилиты уже находится в каталоге fb2conv проекта)
   - скопировать архив проекта в opds/fb2conv (Здесь уже подготовлены shell-скрипты для запуска конвертера) и разархивировать его
   - Для конвертации в MOBI нужно архив с утилитой KindleGen положить в каталог с конвертером и разархивировать
   - В конфигурационном файле sopds.conf задать пути к соответствующим скриптам:
     fb2toepub=../fb2conv/fb2epub
     fb2tomobi=../fb2conv/fb2mobi
     temp_dir=/tmp

