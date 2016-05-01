#!/usr/bin/env python

from thunderdome.config import arena_ami, access_cred, secret_cred, \
    s3_prefix, beanstalk_host, game_name, client_prefix

import argparse
import boto
import sys


parser = argparse.ArgumentParser()
parser.add_argument("--gladnum", default=0, type=int, help="How many gladiators you want to spin up. Default it 0")
parser.add_argument("--refnum", default=1, type=int, help="How many referees you want to spin up. Default is 1")
parser.add_argument("--instype", default='c4.large', help="What type of instance to spin up. Default is c4.large")
args = parser.parse_args()

count = args.gladnum
numRefs = args.refnum
instanceType = args.instype

user_data = \
"""#!/bin/bash
su - gladiator << EOF

export ACCESS_CRED='%s'
export SECRET_CRED='%s'
export S3_PREFIX='%s'
export GAME_NAME='%s'
export CLIENT_PREFIX='%s'
export SERVER_HOST='localhost'
export SERVER_PATH='/home/gladiator/arena/Cerveau'
export BEANSTALK_HOST='%s'

rm -rf /home/gladiator/arena
mkdir /home/gladiator/arena
cd /home/gladiator/arena

# gather up the fixed components
wget http://arena.megaminerai.com/gladiator/gladiator_package.tgz
tar -xf gladiator_package.tgz

python gladiator.py '%s'

EOF
""" % (access_cred, secret_cred, s3_prefix, game_name, client_prefix, beanstalk_host, numRefs)

conn = boto.connect_ec2(access_cred, secret_cred)

print "spinning up %i gladiators with %i referees each on %s instances..." % (count, numRefs, instanceType)
gladiator_image = conn.get_image(arena_ami)
reservation = gladiator_image.run(min_count=count, max_count=count,
                                  user_data=user_data,
                                  instance_type=instanceType,
                                  key_name='arena_head',
                                  security_group_ids=['sg-572ac82c'],
                                  subnet_id='subnet-de7cd0f5') 

print user_data
