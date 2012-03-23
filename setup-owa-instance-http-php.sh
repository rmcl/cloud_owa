#!/bin/bash

tee -a /etc/httpd/conf/httpd.conf <<HTTPDCONF

<VirtualHost *:80>
    DocumentRoot /opt/owa
    ErrorLog logs/owa-error_log
    CustomLog logs/owa-access_log common
</VirtualHost>

HTTPDCONF

tee -a /etc/php.ini <<PHPCONF

error_log = /var/log/php-error.log
date.timezone = "America/Los_Angeles"

PHPCONF


# Autostart apache when the instance boots
sudo /sbin/chkconfig --levels 235 httpd on
sudo service httpd start

