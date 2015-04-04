from thunderdome.config import arena_ami, access_cred, secret_cred, s3_prefix, beanstalk_host, game_name

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

python gladiator.py

EOF
""" % (access_cred, secret_cred, s3_prefix, game_name, beanstalk_host)

print user_data
