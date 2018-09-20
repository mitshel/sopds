На примере ubuntu
Устанавливаем пакет
    
    apt-get install libapache2-mod-wsgi-py3

Прописываем настройки апача по пути /etc/apache2/sites-available/ в существующий конфиг или в новый, например в sopds.conf

    Define sopds_dir /путь_к_папке/sopds
    
    <VirtualHost *:80>
        ServerAdmin sopsd@localhost
        ServerName sopds
        DocumentRoot ${sopds_dir}
        
        ErrorLog ${APACHE_LOG_DIR}/sopds_error.log
        CustomLog ${APACHE_LOG_DIR}/sopds_access.log combined
        
        WSGIScriptAlias / ${sopds_dir}/sopds/wsgi.py
        WSGIDaemonProcess sopds processes=2 threads=15 python-path=${sopds_dir} lang='ru_RU.UTF-8' locale='ru_RU.UTF-8
        WSGIProcessGroup sopds
        WSGIScriptReloading On
        WSGIPassAuthorization On
        
    <Directory ${sopds_dir}/sopds/>
        Require all granted
    </Directory>
    
    <Directory ${sopds_dir}/static/>
        Require all granted
    </Directory>
    
    Alias   /static ${sopds_dir}/static
    </VirtualHost>

Если используется виртуальное окружение

    Define sopds_dir /путь_к_папке/sopds
    
    <VirtualHost *:80>
        ServerAdmin sopsd@localhost
        ServerName sopds
        
        ErrorLog ${APACHE_LOG_DIR}/sopds_error.log
        CustomLog ${APACHE_LOG_DIR}/sopds_access.log combined
    
        WSGIScriptAlias / ${sopds_dir}/sopds/wsgi.py

        WSGIDaemonProcess sopds processes=2 threads=15 display-name=%{GROUP} python-path=${sopds_dir} python-home=${sopds_dir}/env lang='ru_RU.UTF-8' locale='ru_RU.UTF-8
        WSGIProcessGroup sopds
        WSGIScriptReloading On
        WSGIPassAuthorization On
    
    <Directory ${sopds_dir}/sopds/>
        Require all granted
    </Directory>
    
    <Directory ${sopds_dir}/static/>
        Require all granted
    </Directory>
    
    Alias /static ${sopds_dir}/static
    
    </VirtualHost>
    
python-home=${sopds_dir}/env - путь к папке виртуального окружения (в данном примере это /../../sopds/env)

display-name=%{GROUP} - необязательный параметр, меняет имя отображаемое для процеса на wsgi:sopds при использовании команды **ps**

    
Включаем конфиг командой

    sudo a2ensite конфиг_sopds
    
Перезапускаем апач

    sudo service apache2 restart
