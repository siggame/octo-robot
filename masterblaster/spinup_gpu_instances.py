#!/usr/bin/env python

# FIX BEANSTALK_HOST, GAME_NAME, AMI

import bootstrap
from thunderdome.config import arena_ami, access_cred, secret_cred, \
    beanstalk_host, game_name

user_data = \
"""#!/bin/bash
su - gladiator << EOF

export ACCESS_CRED='%s'
export SECRET_CRED='%s'
export S3_PREFIX='siggame-glog'
export GAME_NAME='%s'
export CLIENT_PREFIX='ssh://webserver@megaminerai.com'
export SERVER_HOST='localhost'
export SERVER_PATH='/home/gladiator/arena/server'
export BEANSTALK_HOST='%s'

rm -rf /home/gladiator/arena
mkdir /home/gladiator/arena
cd /home/gladiator/arena

# gather up the fixed components
wget http://arena.megaminerai.com/gladiator_package.tgz
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

print user_data
