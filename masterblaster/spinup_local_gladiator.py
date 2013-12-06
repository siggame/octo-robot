from arena.settings.aws_secrets import access_cred, secret_cred, s3_prefix
from thunderdome.config import game_name, client_prefix, beanstalk_host

import os
import shutil
import subprocess

living_corders = '/home/brandon/Desktop/gladiators/' # this is identical to the gladiator's arena folder
server_path = '/home/brandon/Desktop/gladiators/server'
megaminer_repo = '/home/brandon/Desktop/MegaMinerAI-12'
gladiator_pck = '/home/brandon/Desktop/bArena/gladiator/'

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
shutil.copyfile('/home/brandon/Desktop/bArena/Makefile', living_corders + 'Makefile')
shutil.copyfile('/home/brandon/Desktop/bArena/referee_buildout', living_corders + 'buildout.cfg')
subprocess.call(["make"], cwd=living_corders)

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
../bin/python referee.py $SERVER_PATH  >  ../refere-1.txt &
cd ..
""" % (str(access_cred), str(secret_cred), str(s3_prefix), game_name, client_prefix, 'localhost', server_path, 'localhost')

writer.write(bash_mesg)
writer.close()

subprocess.Popen(['bash', living_corders + 'kick.sh'], cwd=living_corders)

exit()

server = subprocess.Popen(['python', 'main.py', '-arena'], cwd=server_path, stdout=file(server_path + "/server-output.txt", 'w'))

referee_count = 1
refs = []
for i in xrange(referee_count):
    ref_folder = os.path.join(living_corders, "%d" % i)
    os.mkdir(ref_folder)
    shutil.copy2(os.path.join(living_corders, "referee.py"), ref_folder) 
    shutil.copy2(os.path.join(living_corders, "prep_for_bake.py"), ref_folder)
    refs.append(subprocess.Popen(['python', 'referee.py', '$SERVER_PATH'], cwd=ref_folder, stdout=file(living_corders + "/ref-output-%d.txt" % i, 'w')))

"""
rm -rf /home/gladiator/arena
mkdir /home/gladiator/arena
cd /home/gladiator/arena

# gather up the fixed components
# wget http://arena.megaminerai.com/gladiator_package.tgz
# tar -xf gladiator_package.tgz

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

"""
