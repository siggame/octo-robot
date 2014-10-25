from thunderdome.config import game_name
import subprocess
import shutil
import os

file_path = os.path.abspath(__file__)
home_dir = os.path.dirname(file_path)
octo_robot_dir = os.path.dirname(home_dir)


gitrepo = 'git@github.com:siggame/MegaMinerAI-13'
repo_dir = os.path.join(octo_robot_dir, game_name)
server_location = os.path.join(repo_dir, 'server')
gladiator_location = os.path.join(octo_robot_dir, 'gladiator')

if not os.path.exists(repo_dir):
    subprocess.call(['git', 'clone', gitrepo, game_name], cwd=octo_robot_dir)
else:
    subprocess.call(['git', 'pull'], cwd=repo_dir)

gladiator_p_folder = os.path.join(octo_robot_dir, 'gladiator_package')
gladiator_p_server = os.path.join(gladiator_p_folder, 'server')

gladiator_files = os.listdir(gladiator_location)

for i in gladiator_files:
    print i

if os.path.exists(gladiator_p_folder):
    shutil.rmtree(gladiator_p_folder)

os.makedirs(gladiator_p_folder)
shutil.copytree(server_location, gladiator_p_server)
for i in gladiator_files:
    shutil.copy(os.path.join(gladiator_location, i), os.path.join(gladiator_p_folder, i))


shutil.make_archive(gladiator_p_folder, 'gztar', octo_robot_dir, gladiator_p_folder)

