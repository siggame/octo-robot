#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import re
import json
import gzip
import subprocess
import os
import signal
import random
import socket
import md5
import zipfile
from time import sleep
from datetime import datetime
from bz2 import BZ2File

# Non-Django 3rd Party Imports
import beanstalkc
import boto

game_name = os.environ['GAME_NAME'].split("-")[2]
game_name = game_name[0].upper() + game_name[1:len(game_name)]

def main(games_to_play=None):
    stalk = beanstalkc.Connection(host=os.environ['BEANSTALK_HOST'])
    stalk.watch('game-requests-%s' % os.environ['GAME_NAME'])  # input
    stalk.use('game-results-%s' % os.environ['GAME_NAME'])     # output
    while True:
        looping(stalk)

def looping(stalk):
    '''Get a game, process it, repeat'''
    job = stalk.reserve()
    game = json.loads(job.body)
    print "processing game", game['number']

    game['blaster_id'] = socket.gethostname()
    game['referee_id'] = os.getpid()
    game['started'] = str(datetime.now())

    # get latest client code in arena mode.
    # tournament mode uses client code that is already in place
    if 'tournament' not in game:
        for client in game['clients']:
            update_local_repo(client)

    # make empty files for all the output files
    for prefix in [x['name'] for x in game['clients']]:
        for suffix in ['stdout', 'stderr', 'makeout', 'gitout']:
            with file('%s-%s.txt' % (prefix, suffix), 'w') as f:
                f.write('empty')

    # compile the clients
    game['status'] = "Building"
    stalk.put(json.dumps(game))
    job.touch()
    for client in game['clients']:
        client['compiled'] = (compile_client(client) is 0)
        job.touch()
        print "result for make in %s was %s" % (client['name'],
                                                client['compiled'])

    # fail the game if someone didn't compile in arena mode.
    # tournament mode absolutely cannot have failed games.
    # ties are ok, but really annoying
    if not all([x['compiled'] for x in game['clients']]):
        print "failing the game, someone didn't compile"
        game['status'] = "Failed"
        game['completed'] = str(datetime.now())
        push_datablocks(game)
        stalk.put(json.dumps(game))
        job.delete()
        return

    # start the clients
    server_host = os.environ['SERVER_HOST']
    players = list()
    for cl in game['clients']:
        sleep(10)  # ensures ['clients'][0] plays as p0
        players.append(
            subprocess.Popen(['bash', 'run', game_name, '-r', game['number'], '-s', server_host],
                             stdout=file('%s-stdout.txt' % cl['name'], 'w'),
                             stderr=file('%s-stderr.txt' % cl['name'], 'w'),
                             cwd=cl['name']))

    # game is running. watch for gamelog
    print "running...", game['number']
    server_path = os.environ['SERVER_PATH']
    game['status'] = "Running"
    stalk.put(json.dumps(game))
    p0_good = True
    p1_good = True
    glog_done = False
    while p0_good and p1_good and not glog_done:
        job.touch()
        sleep(5)
        p0_good = players[0].poll() is None
        p1_good = players[1].poll() is None
        glog_done = os.access("%s/output/gamelogs/%s-%s.json.gz" %
                              (server_path, game_name, game['number']), os.F_OK)

    for x in players:
      try:
        print "*************************************** die", x.pid
        #os.killpg(x.pid, signal.SIGTERM)
        subprocess.call(['kill', '-9', str(x.pid)], cwd=client['name'],
                    stdout=file("/dev/null", "w"),
                    stderr=subprocess.STDOUT)
      except OSError as e:
        print "it didn't dieeee!!!", e
        pass

    print "pushing data blocks...", game['number']
    push_datablocks(game)

    if not glog_done:  # no glog, game did not terminate correctly
        print "game %s early termination, broken client" % game['number']
        game['status'] = "Failed"
        game['completed'] = str(datetime.now())
        if not p0_good:
            game['clients'][0]['broken'] = True
        if not p1_good:
            game['clients'][1]['broken'] = True
        stalk.put(json.dumps(game))
        job.delete()
        return

    # figure out who won by reading the gamelog
    print "determining winner..."
    winner = parse_gamelog(game['number'])
    if winner == '2':
        game['tied'] = True
        print game['clients'][0]['name'], "and", \
            game['clients'][1]['name'], "tied!"
    else:
        if winner == '0':
            game['winner'] = game['clients'][0]
            game['loser'] = game['clients'][1]
        elif winner == '1':
            game['winner'] = game['clients'][1]
            game['loser'] = game['clients'][0]
        print game['winner']['name'], "beat", game['loser']['name']

    # clean up
    print "pushing gamelog..."
    push_gamelog(game)
    game['status'] = "Complete"
    game['completed'] = str(datetime.now())
    stalk.put(json.dumps(game))
    job.delete()
    print "%s done %s" % (game['number'], str(datetime.now()))


def compile_client(client):
    ''' Compile the client and return the code returned by make '''
    print 'Making %s/%s' % (os.getcwd(), client['name'])
    subprocess.call(['make', 'clean'], cwd=client['name'],
                    stdout=file("/dev/null", "w"),
                    stderr=subprocess.STDOUT)
    return subprocess.call(['make'], cwd=client['name'],
                           stdout=file("%s-makeout.txt" % client['name'], "w"),
                           stderr=subprocess.STDOUT)


def parse_gamelog(game_number):
    ''' Determine winner by parsing that last s-expression in the gamelog
        the gamelog is now compressed. '''
    server_path = os.environ['SERVER_PATH']
    with gzip.open("%s/output/gamelogs/%s-%s.json.gz" % (server_path, game_name, game_number), 'rb') as f:
        log = f.read()
    parsed = json.loads(log)
    winners = parsed['winners']
    losers = parsed['losers']
    realWinner = None
    for winner in winners:
        if realWinner is None:
            realWinner = winner['index']
        else:
            return '2' # there was more than one winner, so it's a tie

    if len(losers) == 2:
        return '2' # again, a tie
    
    if realWinner != None:
        return str(realWinner)

    return None


def push_file(local_filename, remote_filename):
    ''' Push this thing to s3 '''
    bucket_name = "%s-%s" % (os.environ['S3_PREFIX'], os.environ['GAME_NAME'])
    access_cred = os.environ['ACCESS_CRED']
    secret_cred = os.environ['SECRET_CRED']
    if access_cred == 'None' or secret_cred == 'None':
        return "None"
    c = boto.connect_s3(access_cred, secret_cred)
    b = c.get_bucket(bucket_name)
    k = boto.s3.key.Key(b)
    k.key = 'logs/%s/%s' % (os.environ['GAME_NAME'], remote_filename)
    k.set_contents_from_filename(local_filename)
    k.set_acl('public-read')
    return "http://%s.s3.amazonaws.com/%s" % (bucket_name, k.key)


def push_datablocks(game):
    ''' Make zip files containing client data and push them to s3 '''
    for client in game['clients']:
        in_name = "%s-data.zip" % client['name']
        with zipfile.ZipFile(in_name, 'w', zipfile.ZIP_DEFLATED) as z:
            for suffix in ['stdout', 'stderr', 'makeout', 'gitout']:
#            for suffix in ['makeout', 'gitout']:
                z.write('%s-%s.txt' % (client['name'], suffix))
        salt = md5.md5(str(random.random())).hexdigest()[:5]
        remote = "%s-%s-%s-data.zip" % (game['number'], salt, client['name'])
        client['output_url'] = push_file(in_name, remote)
        os.remove(in_name)


def push_gamelog(game):
    '''Push gamelog to S3'''
    server_path = os.environ['SERVER_PATH']
    gamelog_filename = "%s/output/gamelogs/%s-%s.json.gz" % (server_path, game_name, game['number'])
    # salt exists to stop people from randomly probing for files
    salt = md5.md5(str(random.random())).hexdigest()[:5]
    remote = "%s-Anarchy-%s.json.gz" % (game['number'], salt)
    game['gamelog_url'] = push_file(gamelog_filename, remote)
    os.remove(gamelog_filename)


def update_local_repo(client):
    '''Get the appropriate code and version from the repository'''
    base_path = os.environ['CLIENT_PREFIX']
    subprocess.call(['rm', '-rf', client['name']],
                    stdout=file('/dev/null'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'clone',
                     '%s%s' % (base_path, client['repo']), client['name']],
                    stdout=file('%s-gitout.txt' % client['name'], 'w'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'checkout', 'master'], cwd=client['name'],
                    stdout=file('%s-gitout.txt' % client['name'], 'a'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'pull'], cwd=client['name'],
                    stdout=file('%s-gitout.txt' % client['name'], 'a'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'checkout', client['tag']],
                    stdout=file('%s-gitout.txt' % client['name'], 'a'),
                    stderr=subprocess.STDOUT,
                    cwd=client['name'])


if __name__ == "__main__":
    main()
