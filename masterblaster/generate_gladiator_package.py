from thunderdome.config import game_name
import subprocess
import shutil
import os
import sys


def generate_package(megaminer_repo):
    file_path = os.path.abspath(__file__)
    home_dir = os.path.dirname(file_path)
    octo_robot_dir = os.path.dirname(home_dir)

    gitrepo = 'git@github.com:siggame/%s' % megaminer_repo
    repo_dir = os.path.join(octo_robot_dir, game_name)
    server_location = os.path.join(repo_dir, 'Cerveau')
    #creer_location = os.path.join(repo_dir, 'Creer')
    #dossier_location = os.path.join(repo_dir, 'Dossier')
    #joueurCpp_location = os.path.join(repo_dir, 'Joueur.cpp')
    #joueurCs_location = os.path.join(repo_dir, 'Joueur.cs')
    #joueurJava_location = os.path.join(repo_dir, 'Joueur.java')
    #joueurJs_location = os.path.join(repo_dir, 'Joueur.js')
    #joueurLua_location = os.path.join(repo_dir, 'Joueur.lua')
    #joueurPy_location = os.path.join(repo_dir, 'Joueur.py')
    gladiator_location = os.path.join(octo_robot_dir, 'gladiator')
    
    if not os.path.exists(repo_dir):
        git_clone_id = subprocess.call(['git', 'clone', '--recursive', gitrepo, game_name], cwd=octo_robot_dir)
        if git_clone_id != 0:
            print "error on clone exiting"
            return
        subprocess.call(['npm', 'install'], cwd=server_location)
        #subprocess.call(['npm', 'install'], cwd=creer_location)
        #subprocess.call(['npm', 'install'], cwd=dossier_location)
        #subprocess.call(['npm', 'install'], cwd=joueurCpp_location)
        #subprocess.call(['npm', 'install'], cwd=joueurCs_location)
        #subprocess.call(['npm', 'install'], cwd=joueurJava_location)
        #subprocess.call(['npm', 'install'], cwd=joueurJs_location)
        #subprocess.call(['npm', 'install'], cwd=joueurLua_location)
        #subprocess.call(['npm', 'install'], cwd=joueurPy_location)
    else:
        subprocess.call(['git', 'pull'], cwd=repo_dir)

        

    gladiator_p_folder = os.path.join(octo_robot_dir, 'gladiator_package')
    gladiator_p_server = os.path.join(gladiator_p_folder, 'Cerveau')
        
    gladiator_files = os.listdir(gladiator_location)

    if os.path.exists(gladiator_p_folder):
        shutil.rmtree(gladiator_p_folder)

    os.makedirs(gladiator_p_folder)
    shutil.copytree(server_location, gladiator_p_server)
    for i in gladiator_files:
        shutil.copy(os.path.join(gladiator_location, i), os.path.join(gladiator_p_folder, i))



def main():
    print sys.argv
    if len(sys.argv) < 2:
        print "Requires location of megmainer ai repo"
        print "Also ensure that this machine and ssh clone access to the repo"
        return

    generate_package(sys.argv[1])
    # shutil.make_archive(gladiator_p_folder, 'gztar', octo_robot_dir, gladiator_p_folder)

    # print gladiator_p_folder
    # subprocess.call(['tar', 'cvf', 'gladiator_package.tgz', '*'], cwd=gladiator_p_folder)
    # subprocess.call(['mv', 'gladiator_package.tgz', '../.'], cwd=gladiator_p_folder)

if __name__ == "__main__":
    main()
