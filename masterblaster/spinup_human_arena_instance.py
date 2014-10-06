#!/usr/bin/env python

from thunderdome.config import arena_ami, access_cred, secret_cred, \
    s3_prefix, beanstalk_host, game_name

user_data = \
"""#!/bin/bash
su - gladiator << EOF

export ACCESS_CRED='%s'
export SECRET_CRED='%s'
export S3_PREFIX='%s'
export GAME_NAME='%s'
export CLIENT_PREFIX='ssh://webserver@megaminerai.com'
export SERVER_HOST='localhost'
export SERVER_PATH='/home/gladiator/arena/server'
export BEANSTALK_HOST='%s'

rm -rf /home/gladiator/arena
mkdir /home/gladiator/arena
cd /home/gladiator/arena

# gather up the fixed components
wget http://54.83.195.22/gladiator/gladiator_package.tgz
tar -xf gladiator_package.tgz

#cd server
#python main.py -arena > ../server-output.txt &
#cd ..

#mkdir 1
#ln human_referee.py 1/referee.py
#ln prep_for_bake.py 1/prep_for_bake.py
#cd 1
#./referee.py $SERVER_PATH &
#cd ..

#mkdir 2
#ln human_referee.py 2/referee.py
#ln prep_for_bake.py 2/prep_for_bake.py
#cd 2
#./referee.py $SERVER_PATH &
#cd ..

EOF
""" % (access_cred, secret_cred, s3_prefix, game_name, beanstalk_host)

import boto

count = 1
print "spinning up %i gladiators..." % count
conn = boto.connect_ec2(access_cred, secret_cred)
gladiator_image = conn.get_image(arena_ami)
reservation = gladiator_image.run(min_count=count, max_count=count,
                                  user_data=user_data,
                                  instance_type='c3.large',
                                  key_name='ARENA_MND_KEY',
                                  security_groups=['gladiator_sec_group'])

print user_data
