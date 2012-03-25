'''
Script to configure and launch Open Web Analytics cluster on EC2.
Author: Russell McLoughlin (russmcl@gmail.com)


commands:
  start
  stop

  set_max_nodes

'''
import sys
import argparse
import logging
from treedict import TreeDict
import boto 
from boto.ec2.elb import HealthCheck

class CloudOwa(object):

    def __init__(self):
        c = TreeDict()
        c.owa.ec2.region = 'us-east-1'
        c.owa.ec2.avail_zon = 'us-east-1c'
        c.owa.ec2.security_group_name = 'owa'
        c.owa.ec2.key_name = 'rmcl'

        c.owa.master_name = 'owa-master'
        c.owa.master_vol_name = 'owa-master-db'
        
        # Size in MB of the ebs volume
        self.c.owa.master_vol_size = 1024

        self.c = c

        # Connect to EC2 
        # AWS access key and AWS secret key are passed in to the method explicitly.
        # Alternatively, you can set the environment variables
        self.con = boto.connect_ec2()

        # Connect to EC2 Load Balancer end point
        self.lb_con = boto.connect_elb()



    def start(self):

        # Determine if cluster is already running
        master_inst = self.get_master_inst()
        
        if master_inst is not None:
            raise Exception, 'Cannot start Cloud OWA cluster because it is already running.'
        
        # Check if securit group exists, if not create it
        self.create_security_group()

        # Create master inst and attach ebs db volume
        self.create_master_inst()

        # Create load balancer
        self.create_load_balancer()

        # Create auto-scaling group for slaves

        
        

    def stop(self):

        # Terminate slaves, first persisting their local event logs to the master db

        # Terminate load balancer

        # Terminate master
        pass


    def create_load_balancer(self):
        '''Create a load balancer for owa slaves if it does not already exist.'''

        # See if the load balancer for owa already exists
        try:
            self.lb_con.get_all_load_balancers('owa-lb')
        except boto.exception.EC2ResponseError:
            logging.info('Load balancer for OWA does not exist. Creating.')
            # Load balancer does not exist
            pass

    def create_master_inst(self):
        '''Create the master instance and attach master db volume to it.'''

        # Check if master database volume exist, else create it
        vol = self.create_master_volume()

        logging.info('Creating master instance')

        # Create the instance
        # TODO(rmcl): CHANGE THIS TO USE OUR CUSTOM AMI WITH BASE DEPENDENCIES
        res = con.run_instances('ami-1b814f72',
                  key_name=self.c.owa.ec2.key_name,
                  instance_type='m1.small',
                  placement=self.c.owa.ec2.avail_zon,
                  security_groups=[self.c.owa.ec2.security_group_name])

        instance = res.instances[0]
        
        # Tag the instance as master 
        con.create_tags([instance.id], {"Name": "owa-master"})

        logging.info('Attaching volume to master instance.')

        # Attach master volume as /dev/sdh
        vol.attach(instance.id, '/dev/sdh')

    def create_master_volume(self):
        '''Create master ebs volume'''
        master_vol = self.get_volume_by_name(self.c.owa.master_vol_name)
        if master_vol == None:
            logging.info('Master database volume does not exist; creating.')
            
            master_vol = self.con.create_volume(self.c.owa.master_vol_size, self.c.owa.ec2.avail_zon)
            con.create_tags(master_vol.id, {"Name": "owa-master-db"})

        return master_vol

    def create_security_group(self):
        '''create a security group for owa if it does not exist.'''
        
        try:
            args = {'groupnames': [self.c.owa.ec2.security_group_name]}
            security_group = self.con.get_all_security_groups(**args)[0]
            print security_group.rules
            return True

        except boto.exception.EC2ResponseError:
            # The group does not exist so we need to create it and authorize traffic
            # on port 22, 80 from the internet and 3306 within the group.
            logging.info('Security group does not exist. Creating.')

            raise NotImplementedError, 'Must add code to create security group.'

        return False

    def get_master_inst(self):
        '''
        Return a reference to the master owa/db server instance.
        If no master instance is running return None
        '''
        insts = self.get_inst_by_name(self.c.owa.master_name)
        if len(insts) == 0:
            return None
        elif len(insts) == 1:
            return insts[0]
        else:
            raise Exception, "Multiple OWA master nodes."

    def get_inst_by_name(self, name):
        '''Return a list of instances that match a specified tag name.'''
        reservations = self.con.get_all_instances()
        instances = [i for r in reservations for i in r.instances]
        
        insts = []
        for i in instances:
            if self.c.owa.master_name == i.tags['Name']:
                insts.append(i)

        return insts

    def get_volume_by_name(self, name):
        '''Return the volume that match a specified tag name or None.'''
        for v in self.con.get_all_volumes():
            if name == v.tags['Name']:
                return v

        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Manage your cloud instance of Open Web Analytics.')
    parser.add_argument('command', metavar='cmd', type=str,
                        help='The command to run.')

    args = parser.parse_args()

    co = CloudOwa()
    if args.command == 'start':
        #co.start()
        print co.get_volume_by_name('owa-master-db')

    elif args.command == 'stop':
        #co.stop()
        pass
    else:
        raise Exception, 'Unknown command, %s.' % (args.command)
