# Author: Russell McLoughlin (russmcl@gmail.com)
#
# launch small instance to do this config:
# ec2-run-instances ami-1b814f72 --instance-type m1.small --region us-east-1 -z us-east-1c -k rmcl -g owa
#
#


# Update apt-get sources and check for security updates.
yum update -y

# Install Apache, PHP, MYSQL
yum -y install emacs screen
yum -y install gcc make
yum -y install httpd mod_ssl
yum -y install mysql-server mysql 
yum -y install php php-dev php-pear php-gd php-mysql php-pcre
yum -y install xfsprogs




# Run the Mysql setup script

exit 1;



# mount the volume to /data
mkdir /data
echo "/dev/xvdh /data xfs noatime 0 0" | sudo tee -a /etc/fstab
mount /data

# Configure MySQL to store database on the new volume
/etc/init.d/mysql stop

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

/etc/init.d/mysql start