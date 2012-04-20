#!/usr/bin/env python

# FIX BEANSTALK_HOST, GAME_NAME, AMI

from config import arena_ami, access_cred, secret_cred, \
                   beanstalk_host, game_name

user_data = \
"""#!/bin/bash
su - gladiator << EOF

export ACCESS_CRED='%s'
export SECRET_CRED='%s'
export S3_PREFIX='siggame-glog'
export GAME_NAME='%s'
export CLIENT_PREFIX='ssh://r99acm.device.mst.edu:2222'
export SERVER_HOST='localhost'
export SERVER_PATH='/home/gladiator/arena/server'
export BEANSTALK_HOST='%s'

rm -rf /home/gladiator/arena
mkdir /home/gladiator/arena
cd /home/gladiator/arena

# gather up the fixed components
wget http://space.arena.megaminerai.com/gladiator_package.tgz
tar -xf gladiator_package.tgz

cd server
python main.py -arena > ../server-output.txt &
cd ..

mkdir 1
ln referee.py 1/referee.py
ln prep_for_bake.py 1/prep_for_bake.py
cd 1
./referee.py $SERVER_PATH &
cd ..

mkdir 2
ln referee.py 2/referee.py
ln prep_for_bake.py 2/prep_for_bake.py
cd 2
./referee.py $SERVER_PATH &
cd ..

EOF
""" % (access_cred, secret_cred, game_name, beanstalk_host)

import boto

count = 1
print "spinning up %i gladiators..." % count
conn = boto.connect_ec2(access_cred, secret_cred)
gladiator_image = conn.get_image(arena_ami)
reservation = gladiator_image.run(min_count = count, max_count = count,
                                  user_data = user_data,
                                  instance_type='c1.medium', 
                                  key_name = 'MND_EC2_keypair',
                                  security_groups = ['MND_SSH'])
