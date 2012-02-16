#!/usr/bin/env python
"""
Missouri S&T ACM SIG-Game Arena (Thunderdome) This is the referee code.
The referee is responsible for compiling the clients, starting the clients
and recovering from the aftermath

@author: Matthew Nuckols <mannr4@mst.edu>
"""
#####

from datetime import datetime

import sys
if len(sys.argv) != 2:
    print "referee.py server_path"
    exit()
else:
    (junk, server_path) = sys.argv

# Some magic to get a standalone python program hooked in to django
import sys
sys.path = ['/home/gladiator', '/home/gladiator/djangolol'] + sys.path

from django.core.management import setup_environ
import settings

setup_environ(settings)

# Non-Django 3rd Party Imports
import re, json               # special strings
import beanstalkc, git, boto  # networky
import subprocess, os         # shellish
import random, time

# My Imports
from thunderdome.models import Game

from threading import Thread

class Smile_And_Nod(Thread):
    """
    Watches a pipe until it is empty.
    
    @cvar pipe: The pipe to observe
    """
    def __init__(self, pipe):
        Thread.__init__(self)
        self.pipe = pipe
        
    def run(self):
        while True:
            if len(self.pipe.readline()) == 0:
                break


stalk = None

def main():
    """
    Initializer. Connects to the globally shared stalk and starts watching for
    game requests
    """
    global stalk
    stalk = beanstalkc.Connection()
    
    stalk.watch('game-requests')
    while True:
        looping()
    

def looping():
    """
    Recurring job to start games. Attempts to spend a brief period attempting
    to reserve a job. Fetches the newest version of the clients, checks for
    embargoes against the player, then tries to compile the client.

    Once that is complete it tries to start the game and fetch the id of the
    newly created game. It then starts threads to watch the two clients for
    termination.

    To detect game termination this thread will watch the log file for the
    ability to write (which indicates the OS is done with it. The gamelog
    is parsed and then the winner is extracted. 

    Result is written to the database and the job is removed from the beanstalk
    queue.

    @pre: The stalk global is ready to be accessed.
    @post: There has been an attempt at playing a game.
    """ 
    global stalk
    # get a game
    job = stalk.reserve(timeout=2)
    if job is None:
        return
    game_id = json.loads(job.body)['game_id']
    game = Game.objects.get(pk=game_id)
    print "processing game", game_id

    gamedatas = list(game.gamedata_set.all())
    random.shuffle(gamedatas) # even split of p0, p1        

    for x in gamedatas:
        update_local_repo(x.client)
    
    # handle embargoed players
    if any([x.client.embargoed for x in gamedatas]):
        game.status = "Failed"
        game.save()
        job.delete()
        print "failing the game, embargoed player"
        return
    
    # get and compile the clients
    for x in gamedatas:
        x.version = x.client.current_version
        result = compile_client(x.client)
        x.compiled = (result is 0)
        if not x.compiled:
            x.client.embargoed = True
            x.client.save()
        x.save()
        print "result for make in %s was %s" % (x.client.name, x.compiled)

    # handle a failed game
    if not all([x.compiled for x in gamedatas]):
        game.status = "Failed"
        game.save()
        job.delete()
        print "failing the game, someone didn't compile"
        return
    
    players = list()
    
    players.append(subprocess.Popen(['./run', 'localhost'], 
                                    cwd=gamedatas[0].client.name, 
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE))
    
    line = players[-1].stdout.readline()
    match = re.search("Creating game (\d+)", line)
    if match:
        game_number = match.groups()[0]
    else:
        line = players[0].stderr.readline()
        if re.search("Unable to open socket", line):
            print "server is probably down. that's bad."
        else:
            print "unexpected output from client. bail."
        players[0].terminate()
        return

    # Player 0 is special, in that we need to read his output just
    # long enough to get the server game number. Once we have that
    # one datum, we ignore the rest of his output.
    nodder1 = Smile_And_Nod(players[0].stdout)
    nodder1.start()
    nodder2 = Smile_And_Nod(players[0].stderr)
    nodder2.start()    

    players.append(subprocess.Popen(['./run', 'localhost', str(game_number)], 
                                    cwd=gamedatas[1].client.name,
                                    stdout=file("/dev/null", "w"),
                                    stderr=subprocess.STDOUT))

    # game is running. watch for gamelog
    print "running..."
    game.status = "Running"
    game.save()
    print "%s/logs/%s.glog" % (server_path, game_number)
    while not os.access("%s/logs/%s.glog" % (server_path, game_number), 
                        os.F_OK):
        job.touch()
        time.sleep(10)
    
    time.sleep(1)

    # figure out who won by reading the gamelog
    print "determining winner..."
    winner = parse_gamelog(game_number)
    if winner == '0':
        game.winner = gamedatas[0].client
        game.loser  = gamedatas[1].client
        gamedatas[0].won = True
        gamedatas[1].won = False
    elif winner == '1':
        game.winner = gamedatas[1].client
        game.loser  = gamedatas[0].client
        gamedatas[0].won = False
        gamedatas[1].won = True
    [x.save() for x in gamedatas]        

    # clean up
    print "cleaning up..."
    [x.terminate() for x in players]
    [x.join() for x in (nodder1, nodder2)]
    print "pushing gamelog..."
    push_gamelog(game, game_number)
    game.status = "Complete"
    game.completed = datetime.now()
    
    game.save()
    job.delete()
    print "done %s" % str(datetime.now())

    
def compile_client(client):
    """
    Launches a sub process which runs make on the specified client
    
    @cvar client: A Client object which we would like to try and compile.   
    """
    return subprocess.call(['make'], cwd=client.name,
                           stdout=file("/dev/null", "w"),
                           stderr=subprocess.STDOUT)


from bz2 import BZ2File
def parse_gamelog(game_number):
    """
    Given a specified game_number, accesses that log and unpacks it, then
    searches the log for the the winner.

    @param game_number: The log to access.
    @return The player number who won, or none if the operation fails.
    """
    ### Determine winner by parsing that last s-expression in the gamelog
    ### the gamelog is now compressed.
    f = BZ2File("%s/logs/%s.glog" % (server_path, game_number), 'r')
    log = f.readline()
    f.close()
    match = re.search("\"game-winner\" (\d+) \"[^\"]+\" (\d+)", log)
    if match:
        return match.groups()[1]
    return None


import md5
    
def push_gamelog(game, game_number):
    """
    Pushes a gamelog to an Amazon S3 Storage Bucket.
    
    @param game: The game model that should be updated with the url of the
        uploaded file.
    @param game_number: The number of the game, which is resolved to be the
        name of the log.

    @pre: Both the game and the log exist
    @post: The log is uplaoded to S3 and the the game model is updated with
        the url of the uploaded file.
    """
    ### Push the gamelog to S3
    bucket_name = os.environ['S3_BUCKET']
    access_cred = os.environ['ACCESS_CRED']
    secret_cred = os.environ['SECRET_CRED']
    c = boto.connect_s3(access_cred, secret_cred)
    b = c.get_bucket(bucket_name)
    k = boto.s3.key.Key(b)

    salt = md5.md5(str(random.random())).hexdigest()[:5]
    k.key = "%s-%s.glog" % (game.pk, salt)
    
    k.set_contents_from_filename("%s/logs/%s.glog" % \
                                     (server_path, game_number))
    k.set_acl('public-read')
    game.gamelog_url = 'http://%s.s3.amazonaws.com/%s' % (bucket_name, k.key)
    game.save()
    os.remove("%s/logs/%s.glog" % (server_path, game_number))
    
    
def update_local_repo(client):
    """
    Updates this referee's copy of the player's code.
    
    @param client: The player whose code we should try to pull.
    @pre: None
    @post: If the code has changed, the client in question will have its
        embargo flag cleared.
    """
    base_path = os.environ['CLIENT_PREFIX']
    subprocess.call(['git', 'clone',                           # might fail
                     '%s/%s.git' % (base_path, client.name)],  # don't care
                    stdout=file('/dev/null', 'w'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'pull'], cwd=client.name,
                    stdout=file('/dev/null', 'w'),
                    stderr=subprocess.STDOUT)                    
    
    # maybe we can unembargo
    repo = git.Repo(client.name)
    if( repo.heads.master.commit.hexsha != client.current_version ):
        client.current_version = repo.heads.master.commit.hexsha
        client.embargoed = False
        client.save()
    
main()
