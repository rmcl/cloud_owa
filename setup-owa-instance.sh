# Author: Russell McLoughlin (russmcl@gmail.com)
#
# Install neccessary software on the instance to run apache, mysql, php and owa.
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



