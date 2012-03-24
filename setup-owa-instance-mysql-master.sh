# SETUP MySQL on this instance to store data on a EBS volume


# mount the volume to /data
mkdir /data
echo "/dev/sdh /data xfs noatime 0 0" | sudo tee -a /etc/fstab
mount /data

# Configure MySQL to store database on the new volume
service mysqld stop

# Remove default mysql directories
rm -rf /etc/mysql
rm -rf /var/lib/mysql
rm -rf /var/log/mysql

# Create empty directories in their place.
mkdir /etc/mysql
mkdir /var/lib/mysql
mkdir /var/log/mysql

# mount /data directories over the new directories
echo "/data/etc/mysql /etc/mysql     none bind" | tee -a /etc/fstab
mount /etc/mysql

echo "/data/lib/mysql /var/lib/mysql none bind" | tee -a /etc/fstab
mount /var/lib/mysql

echo "/data/log/mysql /var/log/mysql none bind" | tee -a /etc/fstab
mount /var/log/mysql

service mysqld start