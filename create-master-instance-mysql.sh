#!/bin/bash
#
# Setup instance to mount MySQL on EBS volume
# 

# Setup MYSQL to use the EBS volume for storate

#
# Attach the volume and create the filesystem
#

# Assume we have attached the mysql EBS volume to /dev/sdh
mkfs.xfs /dev/sdh

# mount the volume to /data
mkdir /data
echo "/dev/sdh /data xfs noatime 0 0" | sudo tee -a /etc/fstab
mount /data

# Configure MySQL to store database on the new volume
service mysqld stop

mkdir /data/etc /data/lib /data/log
mv /etc/mysql     /data/etc/
mv /var/lib/mysql /data/lib/
mv /var/log/mysql /data/log/

mkdir /etc/mysql
mkdir /var/lib/mysql
mkdir /var/log/mysql

echo "/data/etc/mysql /etc/mysql     none bind" | tee -a /etc/fstab
mount /etc/mysql

echo "/data/lib/mysql /var/lib/mysql none bind" | tee -a /etc/fstab
mount /var/lib/mysql

echo "/data/log/mysql /var/log/mysql none bind" | tee -a /etc/fstab
mount /var/log/mysql

# Start MySQL
service mysqld start

# Create my.cnf
tee -a /etc/my.cnf <<MYSQLCONF

[mysqld_safe]
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid

[mysqld]
datadir=/var/lib/mysql
socket=/var/lib/mysql/mysql.sock
user=mysql
# Disabling symbolic-links is recommended to prevent assorted security risks
symbolic-links=0

port=3306

MYSQLCONF

# Get instance IP
INST_IP_ADDRESS=`/sbin/ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'`

echo "bind-address=$INST_IP_ADDRESS" >> /etc/my.cnf



# Create a database for OWA and grante user "owauser" access.
mysql -u root <<MYSQLEXEC

create database owa;
grant usage on *.* to 'owauser'@'%' identified by 'Xa312u';
grant all privileges on owa.* to owauser@'%';

MYSQLEXEC

# Run the mysql secure script
# This will prompt you to set the mysql root password
# we perform this step after creating the owa database so we don't have to
# re-enter the mysql root passsword.
mysql_secure_installation