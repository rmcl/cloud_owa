#
# Setup instance to mount MySQL on EBS volume
# 


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