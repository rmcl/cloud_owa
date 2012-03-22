'''
Script to configure and launch Open Web Analytics cluster on EC2.

Author: Russell McLoughlin (russmcl@gmail.com)
'''
from treedict import TreeDict
import boto 


# CONFIG
c = TreeDict()
c.owa.ec2.region = 'us-east-1'
c.owa.ec2.avail_zon = 'us-east-1c'
c.owa.ec2.security_group_name = 'owa'


# Connect to EC2 
# AWS access key and AWS secret key are passed in to the method explicitly.
# Alternatively, you can set the environment variables
con = boto.connect_ec2()


# Create the security group in which the instances will run if it does not 
# already exist.
try:
    args = {'groupnames': [c.owa.ec2.security_group_name]}
    security_group = con.get_all_security_groups(**args)[0]
    print security_group.rules
except boto.exception.EC2ResponseError:
    # The group does not exist so we need to create it and authorize traffic
    # on port 22, 80.
    print 'group not found'

    raise NotImplementedError, 'Must add code to create security group.'


# Create EBS volume for the OWA MySQL database.
# ec2-create-volume -z us-east-1a -s 100

# Launch master OWA and database instance
# 

# Attach database EBS volume to instance
# ec2-attach-volume -d /dev/sdh -i <instance id> <volume id>
