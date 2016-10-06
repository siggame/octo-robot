### Brief overview of this file and how it works.
### As of right now 24-Dec-13 12:30PM this file will create a complete gladiator folder.
### This is done by copying the gladiator folder in the octo-robot git repo and copying
### the server folder from the megaminer_repo location which is specified below. 
### Make sure that the MegaMinerAI git repo is located at the megaminer_repo specified below.
### After the complete gladiator folder has been created just run the kick.sh script
### this can be done by cd living_corders, chmod +x kick.sh, then kick.sh

### now with the fact that there is a generate gladiator package, this will just copy that folder instead
### if it doesn't exist then it will call the generate gladiator package. 


from arena.settings.aws_secrets import access_cred, secret_cred, s3_prefix
from thunderdome.config import game_name, client_prefix, beanstalk_host
from masterblaster.generate_gladiator_package import generate_package


import os
import shutil
import subprocess
import sys


file_path = os.path.abspath(__file__)
home_dir = os.path.dirname(file_path)
octo_robot_dir = os.path.dirname(home_dir)


living_corders = '/home/siggame/gladiator/' # this is identical to the gladiator's arena folder
server_path = os.path.join(living_corders, 'Cerveau')
gladiator_pck = os.path.join(octo_robot_dir, 'gladiator_package')

if not os.path.exists(gladiator_pck):
    generate_package(sys.argv[1])

print "make sure .ssh/config contains proper configuration for ssh key in order to pull gladiators"
print "checking if gladiators folder exists"

if os.path.exists(living_corders):
    print " found housing: %s remove tree" % living_corders
    shutil.rmtree(living_corders)


print "Placing gladiator package at ", living_corders
shutil.copytree(gladiator_pck, living_corders)

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
export LIVING_CORDERS='%s'

cd $SERVER_PATH
node main.js --arena > ../server-output.txt &
cd $LIVING_CORDERS

mkdir 1
ln referee.py 1/referee.py
ln prep_for_bake.py 1/prep_for_bake.py
cd 1
python referee.py 2> ref1.txt &
cd ..

""" % (str(access_cred), str(secret_cred), str(s3_prefix), game_name, client_prefix, 'localhost', server_path, 'localhost', living_corders)

writer.write(bash_mesg)
writer.close()
