#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Some magic to get a standalone python program hooked in to django
import sys, os
sys.path = ['/home/gladiator', '/home/gladiator/djangolol'] + sys.path

from django.core.management import setup_environ
import settings

setup_environ(settings)

# Non-Django 3rd Party Imports
import subprocess
import time

def main():
    start_server()
    start_referee(1, "%s/server" % os.getcwd())
    start_referee(2, "%s/server" % os.getcwd())
    while True:
        time.sleep(1)


def start_server():
    command = ['python', 'main.py', '-arena']
    return subprocess.Popen(command, cwd='server',
                            stdout=file("/dev/null", "w"),
                            stderr=subprocess.STDOUT)

        
def start_referee(ref_id, server_path):
    subprocess.call(['rm', '-rf', str(ref_id)])
    subprocess.call(['mkdir', str(ref_id)])
    subprocess.call(['ln', '../referee.py'], cwd='%s/' % ref_id)
    command = ['./referee.py', server_path]
    return subprocess.Popen(command, cwd=str(ref_id))

#def start_referee(server_path):
#    command = ['./referee.py', server_path]
#    return subprocess.Popen(command)

main()
