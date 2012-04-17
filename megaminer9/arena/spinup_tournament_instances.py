#!/usr/bin/env python


from config import tournament_ami, access_cred, secret_cred, \
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


cd server
python main.py -arena > ../server-output.txt &
cd ..

cd 1
./referee.py $SERVER_PATH &
cd ..

cd 2
./referee.py $SERVER_PATH &
cd ..

EOF
""" % (access_cred, secret_cred, beanstalk_host, game_name)

import boto

count = 10
print "spinning up %i gladiators..." % count
conn = boto.connect_ec2(access_cred, secret_cred)
gladiator_image = conn.get_image(tournament_ami)
reservation = gladiator_image.run(min_count = count, max_count = count,
                                  user_data = user_data,
                                  instance_type='c1.medium', 
                                  key_name = 'MND_EC2_keypair',
                                  security_groups = ['MND_SSH'])
