'''
Script to configure and launch Open Web Analytics cluster on EC2.
Author: Russell McLoughlin (russmcl@gmail.com)


commands:
  start
  stop

  set_max_nodes

'''
from __future__ import with_statement
import time
import logging
import paramiko
import socket
import fabric.contrib.files
from fabric.api import *
from fabric.contrib.files import *
import boto 
from boto.ec2.elb import HealthCheck

# Configure logging options.
LOG = logging.getLogger(__name__)
LOG_handler = logging.StreamHandler()
LOG_formatter = logging.Formatter(fmt='%(asctime)s [%(funcName)s:%(lineno)03d] %(levelname)-5s: %(message)s',
                                  datefmt='%m-%d-%Y %H:%M:%S')
LOG_handler.setFormatter(LOG_formatter)
LOG.addHandler(LOG_handler)
LOG.setLevel(logging.INFO)

# Default Config param

## Fabric Options
env.key_filename = os.path.join(os.environ["HOME"], ".ssh/rmcl")
env.user = 'ec2-user'
env.disable_known_hosts = True
env.no_agent = True
env.port = 22

ENV_DEFAULT = {
    'ec2.avail_zon': 'us-east-1c',
    'ec2.security_group_name': 'owa',
    'ec2.key_name': 'rmcl',

    'owa.master_inst_type': 't1.micro',
    'owa.slave_inst_type': 't1.micro',
    'owa.slave_name': 'owa-slave',
    'owa.master_name': 'owa-master',
    'owa.master_vol_name': 'owa-master-db',
    'owa.lb_name': 'owa-lb',
    'owa.master_vol_size': 1024,

    'ec2.reboot_wait_time': 20,    
    'ec2.status_wait_time': 20
}

# Allow user to specify config file to overide default config.
has_rcfile = os.path.exists(env.rcfile)
for k, v in ENV_DEFAULT.items():
    if not k in env:
        env[k] = v
    if v:
        t = type(v)
        LOG.debug("%s [%s] => %s" % (k, t, env[k]))
        env[k] = t(env[k])


# Connect to EC2

# AWS access key and AWS secret key are passed in to the method explicitly.
# Alternatively, you can set the environment variables
ec2_con = boto.connect_ec2()

# Connect to EC2 Load Balancer end point
ec2_lb_con = boto.connect_elb()

@task
def test():
    inst = __get_inst_by_name__('owa-testinst')[0]

    __waitUntilStatus__(inst, 'running')

    # Configure the master instance
    with settings(host_string=inst.public_dns_name):
        #install_base_packages()
        #configure_slave()
        pass

    instance = inst

    lb = __get_load_balancer__(create = False)
    lb.register_instances([instance.id])

@task
def install_base_packages():
    sudo('yum update -y')

    sudo('yum -y install emacs screen')
    sudo('yum -y install gcc make')
    sudo('yum -y install httpd mod_ssl')
    sudo('yum -y install mysql-server mysql')
    sudo('yum -y install php php-dev php-pear php-gd php-mysql php-pcre')
    sudo('yum -y install xfsprogs')




@task
def start_cluster():
    '''Start the cluster if it is not already running.'''

    master_inst = __get_master_inst__(create = False)
    
    print master_inst

    if master_inst is not None:
        raise Exception, 'Cannot start Cloud OWA cluster because it is already running.'
        
    # Check if securit group exists, if not create it
    sg = __get_security_group__()
    print sg.rules

    # Create master inst and attach ebs db volume
    master_inst = __get_master_inst__(create = True)

    # Configure the master instance
    with settings(host_string=master_inst.public_dns_name):
        run('uptime')
        #configure_apache_php_owa()



    # Create load balancer
    lb = __get_load_balancer__()
    logging.info('Load balancer DNS: %s' % (lb.dns_name))


    print inst


@task
def stop_cluster():
    # Terminate slaves, first persisting their local event logs to the master db

    # Terminate load balancer
    lb = self.get_load_balancer(create = False)
    if lb is not None:
        lb.delete()

    # Terminate master
        pass


@task
def stop_slave_instance():
    # Create the instance
    LOG.info('Stop slave instance.')

@task
def start_slave_instance():
    # Create the instance
    LOG.info('Creating new slave instance')

    # Create the instance
    # TODO(rmcl): CHANGE THIS TO USE OUR CUSTOM AMI WITH BASE DEPENDENCIES
    res = ec2_con.run_instances('ami-1b814f72',
                            key_name=env['ec2.key_name'],
                            instance_type=env['owa.slave_inst_type'],
                            placement=env['ec2.avail_zon'],
                            security_groups=[env['ec2.security_group_name']])

    instance = res.instances[0]

    print instance.id

    # Tag the instance as master 
    ec2_con.create_tags([instance.id], {"Name": env['owa.slave_name']})

    # wait for instance to boot
    LOG.info('Waiting for new instance to boot.')
    __waitUntilStatus__(instance, 'running')

    # Configure apache, php, owa
    LOG.info('boot complete. Configuring instance.')
    with settings(host_string=instance.public_dns_name):
        install_base_packages() # Remove this when we replace custom AMI
        configure_slave()

    # Add new slave to load balancer.
    LOG.info('adding slave to load balancer.')
    lb = __get_load_balancer__(create = False)
    lb.register_instances([instance.id])

@task
def configure_apache_php_owa():
    '''Connect to an instance and set apache, php and owa configuration options.'''

    # Add virtual host to Apache.
    httpd_conf = '''
<VirtualHost *:80>
    DocumentRoot /opt/owa
    ErrorLog logs/owa-error_log
    CustomLog logs/owa-access_log common
</VirtualHost>
'''
    fabric.contrib.files.append('/etc/httpd/conf/httpd.conf',
                                httpd_conf,
                                use_sudo = True)

    # Set timezone and error log for php.
    php_conf = '''
error_log = /var/log/php-error.log
date.timezone = "America/Los_Angeles"
'''
    fabric.contrib.files.append('/etc/php.ini',
                                php_conf,
                                use_sudo = True)



    # Download OWA and move it into position.
    run('wget "http://downloads.openwebanalytics.com/owa/owa_1_5_2.tar"')
    run('tar -xf owa_1_5_2.tar')
    sudo('mv owa /opt/owa_1_5_2')
    sudo('chown -R apache:apache /opt/owa_1_5_2')
    sudo('ln -s /opt/owa_1_5_2 /opt/owa')

    
    master_inst = __get_master_inst__(create = False)
    

    owa_conf = '''<?php
    define('OWA_DB_TYPE', 'mysql');
    define('OWA_DB_NAME', 'owa');
    define('OWA_DB_HOST', '%s');
    define('OWA_DB_USER', 'owauser');
    define('OWA_DB_PASSWORD', 'Xa312u');
    ''' % (master_inst.private_dns_name)

    fabric.contrib.files.append('/opt/owa/owa-config.php',
                                owa_conf,
                                use_sudo = True)
    
    sudo('chown apache:apache /opt/owa/owa-config.php')

    sudo('service httpd restart')

@task
def configure_slave():

    # Perform basic setup of Apache, PHP
    configure_apache_php_owa()

    # Append slave specific OWA config
    owa_slave_conf = '''
    define('OWA_QUEUE_EVENTS', true);
    define('OWA_EVENT_QUEUE_TYPE', 'file');
    '''

    fabric.contrib.files.append('/opt/owa/owa-config.php',
                                owa_slave_conf,
                                use_sudo = True)

    # Add a cron task to process event queue
    cron_line = "0,5,10,15,20,25,30,35,40,45,50,55 * * * * php /opt/owa/cli.php cmd=processEventQueue source=file destination=database"
    fabric.contrib.files.append('/tmp/apache_crontab', cron_line, use_sudo = True)
    sudo('crontab -u apache /tmp/apache_crontab')



def __get_master_inst__(create = True):
    '''
    Return a reference to the master owa/db server instance.
    If no master instance is running and create is False return None
    Else create the instance and attach db ebs volume.
    '''
    insts = __get_inst_by_name__(env['owa.master_name'])
    if len(insts) > 0:
        return insts[0]
    

    # master instance does not exist
    if create is False:
        return None

    # Check if master database volume exist, else create it
    vol = self.get_master_volume()

    logging.info('Creating master instance')

    # Create the instance
    # TODO(rmcl): CHANGE THIS TO USE OUR CUSTOM AMI WITH BASE DEPENDENCIES
    res = con.run_instances('ami-1b814f72',
                            key_name=env['owa.ec2.key_name'],
                            instance_type=env['owa.master_inst_type'],
                            placement=env['ec2.avail_zon'],
                            security_groups=[env['ec2.security_group_name']])

    instance = res.instances[0]
        
    # Tag the instance as master 
    con.create_tags([instance.id], {"Name": "owa-master"})

    logging.info('Attaching volume to master instance.')

    # Attach master volume as /dev/sdh
    vol.attach(instance.id, '/dev/sdh')

def __get_master_volume__(self):
    '''Create master ebs volume'''
    master_vol = self.get_volume_by_name(self.c.owa.master_vol_name)

    if master_vol == None:
        logging.info('Master database volume does not exist; creating.')
            
        master_vol = self.con.create_volume(env['owa.master_vol_size'], env['ec2.avail_zon'])
        con.create_tags(master_vol.id, {"Name": "owa-master-db"})

    return master_vol

def __get_security_group__(self):
    '''create a security group for owa if it does not exist.'''
    
    try:
        args = {'groupnames': [self.c.owa.ec2.security_group_name]}
        security_group = self.con.get_all_security_groups(**args)[0]
        return security_group

    except boto.exception.EC2ResponseError:
        # The group does not exist so we need to create it and authorize traffic
        # on port 22, 80 from the internet and 3306 within the group.
        logging.info('Security group does not exist. Creating.')
        
        raise NotImplementedError, 'Must add code to create security group.'

    return False

def __get_load_balancer__(create = True):
    '''
    Return reference to load balancer. If it does not exist and create is
    true, create a load balancer for owa slaves if it does not already exist.
    '''

    # See if the load balancer for owa already exists
    try:
        return ec2_lb_con.get_all_load_balancers(env['owa.lb_name'])[0]
    except boto.exception.EC2ResponseError:
        # Check arg to determine if we should create load balancer
        if create is False:
            return None

        # Load balancer does not exist
        LOG.info('Load balancer for OWA does not exist. Creating.')
        
        hc = HealthCheck(interval=20,
                         healthy_threshold=3,
                         unhealthy_threshold=5,
                         target='HTTP:80/')

        regions = [env['ec2.avail_zon']]
        ports = [(80, 'http'), (443, 8443, 'tcp')]
        lb = ec2_lb_con.create_load_balancer(env['owa.lb_name'], regions, ports)
        lb.configure_health_check(hc)
        
        return lb

def __get_inst_by_name__(name, running = True):
    '''
    Return a list of instances that match a specified tag name.
    If running is True then only return running instances.
    '''
    reservations = ec2_con.get_all_instances()
    instances = [i for r in reservations for i in r.instances]
    
    insts = []
    for i in instances:
        if name == i.tags['Name']:
            # If running is true only return running instances.
            if not running or i.update() == 'running':
                insts.append(i)
            
    return insts

def __waitUntilStatus__(inst, status):
    tries = 10
    while tries > 0 and not inst.update() == status:
        time.sleep(env["ec2.status_wait_time"])
        tries -= 1
    if tries == 0:
        logging.error("Last '%s' status: %s" % (__getInstanceName__(inst), inst.update()))
        raise Exception("Timed out waiting for %s to get to status '%s'" % (__getInstanceName__(inst), status))
    
    ## Just because it's running doesn't mean it's ready
    ## So we'll wait until we can SSH into it
    if status == 'running':
        # Set the timeout
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(env["ec2.reboot_wait_time"])
        host_status = False
        tries = 5
        LOG.info("Testing whether instance '%s' is ready [tries=%d]" % (__getInstanceName__(inst), tries))
        while tries > 0:
            host_status = False
            try:
                transport = paramiko.Transport((inst.public_dns_name, 22))
                transport.close()
                host_status = True
            except:
                pass
            if host_status: break
            time.sleep(env["ec2.reboot_wait_time"])
            tries -= 1
        ## WHILE
        socket.setdefaulttimeout(original_timeout)
        if not host_status:
            raise Exception("Failed to connect to '%s'" % __getInstanceName__(inst))

def __getInstanceName__(inst):
    assert inst
    return (inst.tags['Name'] if 'Name' in inst.tags else '???')
