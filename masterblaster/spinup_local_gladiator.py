### Brief overview of this file and how it works.
### As of right now 24-Dec-13 12:30PM this file will create a complete gladiator folder.
### This is done by copying the gladiator folder in the octo-robot git repo and copying
### the server folder from the megaminer_repo location which is specified below. 
### Make sure that the MegaMinerAI git repo is located at the megaminer_repo specified below.
### After the complete gladiator folder has been created just run the kick.sh script
### this can be done by cd living_corders, chmod +x kick.sh, then kick.sh


from arena.settings.aws_secrets import access_cred, secret_cred, s3_prefix
from thunderdome.config import game_name, client_prefix, beanstalk_host

import os
import shutil
import subprocess

living_corders = '/home/pi/Desktop/gladiators/' # this is identical to the gladiator's arena folder
server_path = '/home/pi/Desktop/gladiators/server'
megaminer_repo = '/home/pi/Desktop/MegaMinerAI-12'
gladiator_pck = '/home/pi/Desktop/octo-robot/gladiator/'

print "make sure .ssh/config contains proper configuration for ssh key in order to pull gladiators"
print "checking if gladiators folder exists"
if os.path.exists(living_corders):
    print " found housing: %s remove tree" % living_corders
    shutil.rmtree(living_corders)

if os.path.exists(os.path.join(living_corders, "server")):
    print " found server folder: %s removing tree" % server_path
    shutil.rmtree(os.path.join(living_corders, "server"))

if not os.path.exists(megaminer_repo):
    raise Exception("Couldn't find %s make sure the path is correct or git clone the repo" % megaminer_repo)

shutil.copytree(gladiator_pck, living_corders)
shutil.copytree(os.path.join(megaminer_repo, "server"), server_path)
#shutil.copyfile('/home/pi/Desktop/octo-robot/Makefile', living_corders + 'Makefile')
#shutil.copyfile('/home/pi/Desktop/octo-robot/referee_buildout', living_corders + 'buildout.cfg')

writer = open(living_corders + 'kick.sh', 'w')

bash_mesg = """
export ACCESS_CRED='%s'
export SECRET_CRED='%s'
export S3_PREFIX='%s'
export GAME_NAME='%s'
export CLIENT_PREFIX='%s'
export SERVER_HOST='%s'
export SERVER_PATH='%s'
export BEANSTALK_HOST='%s'

cd server
python main.py -arena > ../server-output.txt &
cd ..

mkdir 1
ln referee.py 1/referee.py
ln prep_for_bake.py 1/prep_for_bake.py
cd 1
python referee.py &
cd ..
""" % (str(access_cred), str(secret_cred), str(s3_prefix), game_name, client_prefix, 'localhost', server_path, 'localhost')

writer.write(bash_mesg)
writer.close()
