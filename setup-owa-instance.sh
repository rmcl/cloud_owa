# Author: Russell McLoughlin (russmcl@gmail.com)
#
# launch small instance to do this config:
# ec2-run-instances ami-1b814f72 --instance-type m1.small --region us-east-1 -z us-east-1c -k rmcl -g owa
#
#


# Update apt-get sources and check for security updates.
apt-get update
apt-get upgrade –show-upgraded

# Set the instance timezone
dpkg-reconfigure tzdata

# Install Apache, PHP, MYSQL
# This will prompt you to set the mysql root password
apt-get install apache2 mysql-server php5 php5-dev php-pear php5-gd php5-mysql xfsprogs

# Run the Mysql setup script
mysql_secure_installation



# Setup MYSQL to use the EBS volume for storate

# Attach the volume and create the filesystem
# Assume we have attached the mysql EBS volume to /dev/sdh but it shows up in instances as /dev/xvdh
mkfs.xfs /dev/xvdh


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