На примере ubuntu
    
    Устанавливаем пакет
    
    apt-get install libapache2-mod-wsgi-py3

Прописываем настройки апача по пути /etc/apache2/sites-available/ в существующий конфиг или в новый, например в sopds.conf

    <VirtualHost *:80>
      ServerAdmin webmaster@localhost
      ServerName sopds.yourlib.com
      ErrorLog /var/log/apache2/sopds_error.log
        
      WSGIScriptAlias / /home/sopds/sopds/wsgi.py
      WSGIDaemonProcess sopds processes=2 threads=15 python-path=/home/sopds
      WSGIProcessGroup sopds
      WSGIScriptReloading On
      WSGIPassAuthorization On
      
      <Directory "/home/sopds/sopds/">
        Require all granted
      </Directory>
      
      <Directory "/home/sopds/static/">
        Require all granted
      </Directory>
      
      Alias   /static    "/home/sopds/static"
  </VirtualHost>
  
Если используется виртуальное окружение
