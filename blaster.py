#!/usr/bin/env python
"""
Missouri S&T ACM SIG-Game Arena (Thunderdome)

A task process that starts the referees (who play the matches.)

@author: Matthew Nuckolls <mannr4@mst.edu>
"""

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
    """
    Starts the game server and two threads to referees to play matches.
    """
    start_server()
    start_referee(1, "%s/server" % os.getcwd())
    start_referee(2, "%s/server" % os.getcwd())
    while True:
        time.sleep(1)


def start_server():
    """
    Starts the game server which is responsible for the game logic.
    
    @pre: The game server is configured correctly.   
    @post: A game server thread is started.
    """
    command = ['python', 'main.py', '-arena']
    return subprocess.Popen(command, cwd='server',
                            stdout=file("/dev/null", "w"),
                            stderr=subprocess.STDOUT)

        
def start_referee(ref_id, server_path):
    """
    Cleans up where the the referee will make his home, then starts
    a referee subprocess.
    
    @param ref_id: The identifier for the referee. Unique to the system.
    @param server_path: path to the server.
    """
    subprocess.call(['rm', '-rf', str(ref_id)])
    subprocess.call(['mkdir', str(ref_id)])
    subprocess.call(['ln', '../referee.py'], cwd='%s/' % ref_id)
    command = ['./referee.py', server_path]
    return subprocess.Popen(command, cwd=str(ref_id))

#def start_referee(server_path):
#    command = ['./referee.py', server_path]
#    return subprocess.Popen(command)

main()
