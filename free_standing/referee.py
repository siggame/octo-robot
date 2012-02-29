#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
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
import beanstalkc, boto       # networky
import subprocess, os         # shellish
import random, time

# My Imports
from thunderdome.models import Game

stalk = None

def main():
    global stalk
    stalk = beanstalkc.Connection()
    
    stalk.watch('game-requests')
    while True:
        looping()
    

def looping():
    global stalk
    # get a game
    job = stalk.reserve(timeout=2)
    if job is None:
        return
    game_id = json.loads(job.body)['game_id']
    game = Game.objects.get(pk=game_id)
    print "processing game", game_id

    gamedatas = list(game.gamedata_set.all())
    gamedatas.sort(key = lambda x: x.pk)
    
    for x in gamedatas:
        update_local_repo(x.client)
        
    # make empty files for all the output files
    # FIXME really the zipper should just gather up "%s-*" % x.client.name
    for prefix in [x.client.name for x in gamedatas]:
        for suffix in ['stdout', 'stderr', 'makeout', 'gitout']:
            with file('%s-%s.txt' % (prefix, suffix), 'w') as f:
                f.write('empty')
    
    # handle embargoed players
    if any([x.client.embargoed for x in gamedatas]):
        [x.save() for x in gamedatas]
        game.status = "Failed"
        game.completed = datetime.now()
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
        game.completed = datetime.now()
        game.save()
        job.delete()
        print "failing the game, someone didn't compile"
        push_datablocks(game)
        return
    
    players = list()

    game_number = str(game.pk)
    for x in gamedatas:
        time.sleep(5)
        players.append(
            subprocess.Popen(['bash', 'run', 'localhost', str(game.pk)], 
                             stdout=file('%s-stdout.txt' % x.client.name, 'w'),
                             stderr=file('%s-stderr.txt' % x.client.name, 'w'),
                             cwd=x.client.name))
    

    # FIXME if .poll() is not None then a process has ended
    #       this indicates that it has blown up 
    #       before connecting to the server
    
    # game is running. watch for gamelog
    print "running..."
    game.status = "Running"
    game.save()
    print "%s/logs/%s.glog" % (server_path, game_number)
    while not os.access("%s/logs/%s.glog" % (server_path, game_number), 
                        os.F_OK):
        job.touch()
        time.sleep(10)
    
    # figure out who won by reading the gamelog
    print "determining winner..."
    winner = parse_gamelog(game_number)
    if winner == '0':
        game.winner = gamedatas[0].client
        game.winner.inc_score(1.0)
        game.loser  = gamedatas[1].client
        assign_elo( game.winner, game.loser )
        gamedatas[0].won = True
        gamedatas[1].won = False
    elif winner == '1':
        game.winner = gamedatas[1].client
        game.winner.inc_score(1.0)
        game.loser  = gamedatas[0].client
        assign_elo( game.winner, game.loser )
        gamedatas[0].won = False
        gamedatas[1].won = True
    elif winner == '2':
        [x.client.inc_score(0.5) for x in gamedatas]
    [x.save() for x in gamedatas]        
    
    # clean up
    print "cleaning up..."
    [x.terminate() for x in players]
    #[x.join() for x in (nodder1, nodder2, nodder3, nodder4)]
    print "pushing gamelog..."
    push_gamelog(game, game_number)
    print "pushing data blocks..."
    push_datablocks(game)
    game.status = "Complete"
    game.completed = datetime.now()    
    game.save()
    job.delete()
    print "%s done %s" % (str(game.pk), str(datetime.now()))

    
def compile_client(client):
    subprocess.call(['make', 'clean'], cwd=client.name,
                    stdout=file("/dev/null", "w"),
                    stderr=subprocess.STDOUT)
    return subprocess.call(['make'], cwd=client.name,
                           stdout=file("%s-makeout.txt" % client.name, "w"),
                           stderr=subprocess.STDOUT)


from bz2 import BZ2File
def parse_gamelog(game_number):
    ### Determine winner by parsing that last s-expression in the gamelog
    ### the gamelog is now compressed.
    f = BZ2File("%s/logs/%s.glog" % (server_path, game_number), 'r')
    log = f.readline()
    f.close()
    match = re.search("\"game-winner\" (\d+) \"[^\"]+\" (\d+)", log)
    if match:
        return match.groups()[1]
    return None


def push_file( local_filename, remote_filename ):
    ### Push this thing to S3
    bucket_name = os.environ['S3_BUCKET']
    access_cred = os.environ['ACCESS_CRED']
    secret_cred = os.environ['SECRET_CRED']
    c = boto.connect_s3(access_cred, secret_cred)
    b = c.get_bucket(bucket_name)
    k = boto.s3.key.Key(b)
    k.key = remote_filename
    k.set_contents_from_filename(local_filename)
    k.set_acl('public-read')
    return "http://%s.s3.amazonaws.com/%s" % (bucket_name, k.key)


import md5
import zipfile
def push_datablocks(game):
    gamedatas = list(game.gamedata_set.all())
    for gd in gamedatas:
        in_name = "%s-data.zip" % gd.client.name
        with zipfile.ZipFile(in_name, 'w', zipfile.ZIP_DEFLATED) as z:
            #for suffix in ['stdout', 'stderr', 'makeout', 'gitout']:
            for suffix in ['makeout', 'gitout']:
                z.write('%s-%s.txt' % (gd.client.name, suffix))
        salt = md5.md5(str(random.random())).hexdigest()[:5]
        remote = "%s-%s-%s-data.zip" % (game.pk, salt, gd.client.name)
        url = push_file(in_name, remote)
        gd.output_url = url
        gd.save()
        os.remove(in_name)
        

def push_gamelog(game, game_number):
    """Push gamelog to S3"""
    gamelog_filename = "%s/logs/%s.glog" % (server_path, game_number)
    
    # salt exists to stop people from randomly probing for files
    salt = md5.md5(str(random.random())).hexdigest()[:5]
    remote = "%s-%s.glog" % (game.pk, salt)
    url = push_file(gamelog_filename, remote)
    game.gamelog_url = url
    game.save()
    os.remove(gamelog_filename)

        
def update_local_repo(client):
    base_path = os.environ['CLIENT_PREFIX']
    subprocess.call(['git', 'clone',                       # might fail
                     '%s%s' % (base_path, client.repo),    # don't care
                     client.name],
                    stdout=file('%s-gitout.txt' % client, 'w'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'checkout', 'master'], cwd=client.name,
                    stdout=file('%s-gitout.txt' % client, 'a'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'pull'], cwd=client.name,
                    stdout=file('%s-gitout.txt' % client, 'a'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'checkout', 
                     str(client.current_version)], cwd=client.name,
                    stdout=file('%s-gitout.txt' % client, 'a'),
                    stderr=subprocess.STDOUT)

    
import math
def assign_elo( winner, loser ):
    delta = winner.rating - loser.rating
    exp = (-1 * delta) / 400
    odds = 1 / (1 + math.pow(10, exp))
    if winner.rating < 2100:
        k = 32
    elif winner.rating > 2400:
        k = 12
    else:
        k = 24
    modifier = k * (1 - odds)
    winner.rating += modifier
    loser.rating = max([1, loser.rating - modifier])
    winner.save()
    loser.save()
    
main()
