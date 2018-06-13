На примере ubuntu
Устанавливаем пакет
    
    apt-get install libapache2-mod-wsgi-py3

Прописываем настройки апача по пути /etc/apache2/sites-available/ в существующий конфиг или в новый, например в sopds.conf

    <VirtualHost *:80>
        ServerAdmin sopsd@localhost
        ServerName sopds
        DocumentRoot ##### путь_к_папке/sopds
        
        ErrorLog ${APACHE_LOG_DIR}/sopds_error.log
        CustomLog ${APACHE_LOG_DIR}/sopds_access.log combined
        
        WSGIScriptAlias / /home/z/sopds/sopds/wsgi.py
        WSGIDaemonProcess sopds.loc display-name=%{GLOBAL} processes=2 threads=15 python-path=/home/z/sopds
        WSGIProcessGroup sopds.loc
        WSGIScriptReloading On
        WSGIPassAuthorization On
        WSGIApplicationGroup %{GLOBAL}
        
    <Directory "/home/z/sopds/sopds/">
        Require all granted
    </Directory>
    
    <Directory "/home/z/sopds/static/">
        Require all granted
    </Directory>
    
    Alias   /static    "/home/z/sopds/static"
    </VirtualHost>

Если используется виртуальное окружение

<VirtualHost *:80>
   ServerAdmin sopsd@localhost
   ServerName sopds.loc

   LogLevel warn
#   ErrorLog ${APACHE_LOG_DIR}/sopds_error.log
   ErrorLog /home/z/sopds/opds_catalog/log/sopds_error.log
#   CustomLog ${APACHE_LOG_DIR}/sopds_access.log combined
  CustomLog /home/z/sopds/opds_catalog/log/sopds_access.log combined

   WSGIScriptAlias / /home/z/sopds/sopds/wsgi.py

   WSGIDaemonProcess sopds processes=4 display-name=apache2sopds%{GROUP} python-path=/home/z/sopds python-home=/home/z/sopds/v_sopds/lib/python3.5/site-packages
   WSGIProcessGroup sopds
   WSGIScriptReloading On
   WSGIPassAuthorization On
WSGIApplicationGroup %{GLOBAL}

   <Directory "/home/z/sopds/sopds/">
      Require all granted
   </Directory>
   
   <Directory "/home/z/sopds/static/">
      Require all granted
   </Directory>

   Alias   /static    "/home/z/sopds/static"

</VirtualHost>
