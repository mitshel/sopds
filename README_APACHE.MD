На примере ubuntu
Устанавливаем пакет
    
    apt-get install libapache2-mod-wsgi-py3

Прописываем настройки апача по пути /etc/apache2/sites-available/ в существующий конфиг или в новый, например в sopds.conf

    <VirtualHost *:80>
        ServerAdmin sopsd@localhost
        ServerName sopds
        DocumentRoot /путь_к_папке/sopds
        
        ErrorLog ${APACHE_LOG_DIR}/sopds_error.log
        CustomLog ${APACHE_LOG_DIR}/sopds_access.log combined
        
        WSGIScriptAlias / /путь_к_папке/sopds/sopds/wsgi.py
        WSGIDaemonProcess sopds processes=2 threads=15 python-path=/путь_к_папке/sopds
        WSGIProcessGroup sopds
        WSGIScriptReloading On
        WSGIPassAuthorization On
        
    <Directory "/путь_к_папке/sopds/sopds/">
        Require all granted
    </Directory>
    
    <Directory "/путь_к_папке/sopds/static/">
        Require all granted
    </Directory>
    
    Alias   /static    "/путь_к_папке/sopds/static"
    </VirtualHost>

Если используется виртуальное окружение

<VirtualHost *:80>
   ServerAdmin sopsd@localhost
   ServerName sopds

   ErrorLog ${APACHE_LOG_DIR}/sopds_error.log
CustomLog ${APACHE_LOG_DIR}/sopds_access.log combined

   WSGIScriptAlias / /путь_к_папке/sopds/sopds/wsgi.py

   WSGIDaemonProcess sopds processes=4 python-path=/путь_к_папке/sopds python-home=/путь_к_папке_виртуального_окружения/lib/python3.5/site-packages
   WSGIProcessGroup sopds
   WSGIScriptReloading On
   WSGIPassAuthorization On

   <Directory "/путь_к_папке/sopds/sopds/">
      Require all granted
   </Directory>
   
   <Directory "/путь_к_папке/sopds/static/">
      Require all granted
   </Directory>

   Alias   /static    "/путь_к_папке/sopds/static"

</VirtualHost>
