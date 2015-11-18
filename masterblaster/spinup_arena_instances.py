#!/usr/bin/env python

from thunderdome.config import arena_ami, access_cred, secret_cred, \
    s3_prefix, beanstalk_host, game_name, client_prefix

import sys

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

#python gladiator.py

mkdir 1
ln referee.py 1/referee.py
ln prep_for_bake.py 1/prep_for_bake.py
cd 1
python referee.py &
cd ..

EOF
""" % (access_cred, secret_cred, s3_prefix, game_name, client_prefix, beanstalk_host)

import boto

if len(sys.argv) > 1:
   count = int(sys.argv[1])
else:
   count = 1

print "spinning up %i gladiators..." % count
conn = boto.connect_ec2(access_cred, secret_cred)
gladiator_image = conn.get_image(arena_ami)
reservation = gladiator_image.run(min_count=count, max_count=count,
                                  user_data=user_data,
                                  instance_type='c3.large',
                                  key_name='mmai-16-glad-key',
                                  security_groups=['Arena Gladiator']) 

print user_data
