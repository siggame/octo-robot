#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import re
import requests
import json
import gzip
import subprocess
import os
import time
import signal
import random
import socket
import md5
import zipfile
from time import sleep
from datetime import datetime
#Don't think this is needed anymore, uncomment if it does
#from bz2 import BZ2File 

# Non-Django 3rd Party Imports
import beanstalkc
import boto


test_t = os.environ['GAME_NAME'].split("-")

if len(test_t) == 2:
    game_name = test_t[0]
elif len(test_t) == 3:
    game_name = test_t[2]
else:
    print "Not sure which game to play"
    game_name = test_t
game_name = game_name[0].upper() + game_name[1:len(game_name)]

print "Playing with game: ", game_name




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
    print "Processing game", game['number']

    game['blaster_id'] = socket.gethostname()
    game['referee_id'] = os.getpid()
    game['started'] = str(datetime.now())
    
    # get latest client code in arena mode.
    # tournament mode uses client code that is already in place
    game['status'] = "Building"
    if 'tournament' not in game:
        for client in game['clients']:
            update_local_repo(client)

    # make empty files for all the output files
    for prefix in [x['name'] for x in game['clients']]:
        for suffix in ['stdout', 'stderr', 'makeout', 'gitout']:
            with file('%s-%s.txt' % (prefix, suffix), 'w') as f:
                f.write('empty')
      
    # compile the clients
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
        print "Failing the game, someone didn't compile"
        game['status'] = "Failed"
	game['completed'] = str(datetime.now())
	game['tied'] = False
	game['tie_reason'] = "One or both of the clients didn't compile"
	push_datablocks(game)
	stalk.put(json.dumps(game))
	job.delete()
        return

    # start the clients
    server_host = os.environ['SERVER_HOST']
    players = list()


    for i, cl in enumerate(game['clients']):
        players.append(
            subprocess.Popen(['bash',
                                'run', game_name,
                                '-r', game['number'],
                                '-s', server_host,
                                '-i', str(i),
                                '-n', cl['name']
                             ], 
                             stdout=file('%s-stdout.txt' % cl['name'], 'w'),
                             stderr=file('%s-stderr.txt' % cl['name'], 'w'),
                             cwd=cl['name']))

    
    # make sure both clients have connected
    game_server_ip        = os.environ['SERVER_HOST']
    game_server_status    = requests.get('http://%s:3080/status/%s/%s' %
                            (game_server_ip, game_name, game['number'])).json()
    start_time            = int(round(time.time() * 1000))
    current_time          = start_time
    MAX_TIME              = 10000           # in milliseconds
    
    # block while at least one client is not connected
    while len(game_server_status['clients']) < 2 and (current_time - start_time <= MAX_TIME):
        sleep(.001)        # wait a bit for the clients to connect
        current_time = int(round(time.time() * 1000))
        
        #Not sure if printing this is needed
        #if game_server_status['status'] == "open":
        #    print len(game_server_status['clients'])
        
        
        game_server_status = requests.get('http://%s:3080/status/%s/%s' %
                             (game_server_ip, game_name, game['number'])).json()

    
    # check if we timed out waiting for clients to connect
    if current_time - start_time > MAX_TIME:
        print "Failing the game, only %d clients connected" % (len(game_server_status['clients']))
        kill_clients(players)
	game['status'] = "Failed"
	game['complete'] = str(datetime.now())
	game['tied'] = False
	if len(game_server_status['clients']) == 0:
	    game['tie_reason'] = "Game failed to start, neither client connected."
	    game['clients'][0]['noconnect'] = True
	    game['clients'][1]['noconnect'] = True
	elif len(game_server_status['clients']) == 1:
	    for i, cl in enumerate(game['clients']):
		if cl.name == game_server_status['clients'][0]['name']:
		    pass
		else:
		    reason = ("Game failed to start,", cl.name, "didn't connect.")
		    game['tie_reason'] = ' '.join(reason)
		    game['clients'][i]['noconnect'] = True
	push_datablocks(game)
	stalk.put(json.dumps(game))
	job.delete()
        return
    
    # game is running. watch for gamelog
    print "Running...", game['number']
    server_path = os.environ['SERVER_PATH']
    game['status'] = "Running"
    stalk.put(json.dumps(game))
    """
    p0_good = True
    p1_good = True
    glog_done = False
    
    while p0_good and p1_good and not glog_done:
        print "Monitoring client1 %s client2 %s and gamelog %s" % (str(p0_good), str(p1_good), str(glog_done))
        job.touch()
        sleep(2)
        p0_good = players[0].poll() is None
        p1_good = players[1].poll() is None
        glog_done = os.access("%s/output/gamelogs/%s-%s.json.gz" %
                              (server_path, game_name, game['number']), os.F_OK)
    """
    
    # wait until the game is over
    game_server_status = requests.get('http://%s:3080/status/%s/%s' %
                         (game_server_ip, game_name, game['number'])).json()
    start_time            = int(round(time.time() * 1000))
    current_time          = start_time
    MAX_TIME              = 2000000
    
    while game_server_status['status'] == 'running' and current_time - start_time <= MAX_TIME:
        job.touch()
        sleep(0.1)
        current_time = int(round(time.time() * 1000))
        game_server_status = requests.get('http://%s:3080/status/%s/%s' %
                             (game_server_ip, game_name, game['number'])).json()
	
	
    if current_time - start_time > MAX_TIME:
	print "Failing game, took to long"
	kill_clients(players)
	game['clients'][0]['gamservdied'] = True
	game['clients'][1]['gamservdied'] = True
	game['status'] = "Failed"
        game['completed'] = str(datetime.now())
        game['tied'] = False
	game['tie_reason'] = "The gameserver blew up." 
	push_datablocks(game)
	stalk.put(json.dumps(game))
	job.delete()
        return
    
    
    kill_clients(players)


    game_server_status = requests.get('http://%s:3080/status/%s/%s' %
                             (game_server_ip, game_name, game['number'])).json()
    if 'disconnected' in game_server_status['clients'][0] or 'disconnected' in game_server_status['clients'][1]:  # game did not terminate correctly
        print "game %s early termination, broken client" % game['number']
        game['status'] = "Failed"
        game['completed'] = str(datetime.now())
        game['tied'] = False
        if 'disconnected' in game_server_status['clients'][0]:
            game['clients'][0]['discon'] = True
            reason = ("Early termination because", game_server_status['clients'][0]['name'], "disconnected unexpectedly.")
            game['tie_reason'] = ' '.join(reason)
        if 'disconnected' in game_server_status['clients'][1]:
            game['clients'][1]['discon'] = True
            reason = ("Early termination because", game_server_status['clients'][1]['name'], "disconnected unexpectedly.")
            game['tie_reason'] = ' '.join(reason)
        push_datablocks(game)
        stalk.put(json.dumps(game))
        job.delete()
        return

    # figure out who won
    print "determining winner..."
    if ('won' in game_server_status['clients'][0] and 'won' in game_server_status['clients'][1]) or ('lost' in game_server_status['clients'][0] and 'lost' in game_server_status['clients'][1]):
        game['tied'] = True
        game['tie_reason'] = game['clients'][0]['reason']
        print game['clients'][0]['name'], "and", \
            game['clients'][1]['name'], "tied!"
    else:
        game['tied'] = False
        if 'won' in game_server_status['clients'][0]:
            game['winner'] = game['clients'][0]
            game['loser'] = game['clients'][1]
            game['win_reason'] = game['clients'][0]['reason']
            game['lose_reason'] = game['clients'][1]['reason']
        else:
            game['winner'] = game['clients'][1]
            game['loser'] = game['clients'][0]
            game['win_reason'] = game['clients'][1]['reason']
            game['lose_reason'] = game['clients'][0]['reason']
	print game['winner']['name'], "beat", game['loser']['name']

    # clean up
    print "pushing data blocks...", game['number']
    push_datablocks(game)
    print "pushing gamelog..."
    push_gamelog(game)
    game['status'] = "Complete"
    game['completed'] = str(datetime.now())
    stalk.put(json.dumps(game))
    job.delete()
    print "%s done %s" % (game['number'], str(datetime.now()))
    return


def kill_clients(players):
    for x in players:
	try:
	    print "*************************************** die", x.pid
	    subprocess.call(['kill', '-KILL', '-%s' % (str(x.pid))])
	except OSError as e:
	    print "it didn't dieeee!!!", e
	    pass


def compile_client(client):
    ''' Compile the client and return the code returned by make '''
    print 'Making %s/%s' % (os.getcwd(), client['name'])
    #subprocess.call(['make', 'clean'], cwd=client['name'],
                    #stdout=file("/dev/null", "w"),
                    #stderr=subprocess.STDOUT)
    return subprocess.call(['make'], cwd=client['name'],
                           stdout=file("%s-makeout.txt" % client['name'], "w"),
                           stderr=subprocess.STDOUT)


def push_file(local_filename, remote_filename, is_glog):
    ''' Push this thing to s3 '''
    bucket_name = "%s" % (os.environ['S3_PREFIX'])
    access_cred = os.environ['ACCESS_CRED']
    secret_cred = os.environ['SECRET_CRED']
    if access_cred == 'None' or secret_cred == 'None':
        return "None"
    c = boto.connect_s3(access_cred, secret_cred)
    b = c.get_bucket(bucket_name)
    k = boto.s3.key.Key(b)
    k.key = 'logs/%s/%s' % (os.environ['GAME_NAME'], remote_filename)
    if is_glog:
        k.set_contents_from_filename(local_filename, {'Content-Type': 'application/json; charset=utf-8', 'Content-Encoding': 'gzip'}, policy='public-read')
    else:
        k.set_contents_from_filename(local_filename, policy='public-read')
    return "http://%s.s3.amazonaws.com/%s" % (bucket_name, k.key)


def push_datablocks(game):
    ''' Make zip files containing client data and push them to s3 '''
    for client in game['clients']:
        in_name = "%s-data.zip" % client['name']
        with zipfile.ZipFile(in_name, 'w', zipfile.ZIP_DEFLATED) as z:
            for suffix in ['stdout', 'stderr', 'makeout', 'gitout']:
#            for suffix in ['makeout', 'gitout']: # this should be removed after competition
                z.write('%s-%s.txt' % (client['name'], suffix))
        salt = md5.md5(str(random.random())).hexdigest()[:5]
        remote = "%s-%s-%s-data.zip" % (game['number'], salt, client['name'])
        client['output_url'] = push_file(in_name, remote, False)
        os.remove(in_name)


def push_gamelog(game):
    '''Push gamelog to S3'''
    server_path = os.environ['SERVER_PATH']
    gamelog_filename = "%s/output/gamelogs/%s-%s.json.gz" % (server_path, game_name, game['number'])
    # salt exists to stop people from randomly probing for files
    salt = md5.md5(str(random.random())).hexdigest()[:5]
    remote = "%s-%s-%s.json.gz" % (game['number'], game_name, salt)
    #local_json = "%s/output/gamelogs/%s-%s.json" % (server_path, game_name, game['number'])
    #with gzip.open("%s/output/gamelogs/%s-%s.json.gz" % (server_path, game_name, game['number']), 'rb') as f:
       #log = f.read()
       #local_json_data = open(local_json, 'w')
       #local_json_data.write(log)
       #local_json_data.close()
    #remote_json = "%s-Anarchy-%s.json" % (game['number'], salt)
    game['gamelog_url'] = push_file(gamelog_filename, remote, True)
    #push_file(local_json, remote_json)
    os.remove(gamelog_filename)
    #os.remove(local_json)


def update_local_repo(client):
    '''Get the appropriate code and version from the repository'''
    base_path = os.environ['CLIENT_PREFIX']
    subprocess.call(['rm', '-rf', client['name']],
                    stdout=file('/dev/null'),
                    stderr=subprocess.STDOUT)
    
    numFailed = 0
    while numFailed < 10000:        #try to clone 10000 times
        try:
            print "git clone %s%s client: %s" % (base_path, client['repo'], client['name'])
            subprocess.call(['git', 'clone',
                    '%s%s' % (base_path, client['repo']), client['name']],
                    stdout=file('%s-gitout.txt' % client['name'], 'w'),
                    stderr=subprocess.STDOUT)
            

            subprocess.call(['git', 'checkout', 'master'], cwd=client['name'],
                    stdout=file('%s-gitout.txt' % client['name'], 'a'),
                    stderr=subprocess.STDOUT)
            print "Clone successful!"
            break
        except OSError:
            numFailed += 1      #keep track of how many times 
            print "Clone failed, retrying"
            if numFailed <= 15:
                sleep(0.01)         #Wait 10ms before attempting to clone again
            elif numFailed > 15:
                sleep(.5)
    #if numFailed == 10000:
        #Insert code to handle permanent clone failure here
        #------------------------------------------------------
        #
        #
        #
        #
        #
        #
        #
        #
        #------------------------------------------------------
    subprocess.call(['git', 'pull'], cwd=client['name'],
                    stdout=file('%s-gitout.txt' % client['name'], 'a'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'checkout', client['tag']],
                    stdout=file('%s-gitout.txt' % client['name'], 'a'),
                    stderr=subprocess.STDOUT,
                    cwd=client['name'])
    print "Checking out ", client['tag']


if __name__ == "__main__":
    main()
