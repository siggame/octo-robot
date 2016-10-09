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

while True:
    print "Getting external IP"
    try:
        url = 'http://ifconfig.co'
        headers = {'Accept': 'application/json'}
        readin = requests.get(url, headers=headers, timeout=10)
        external_ip = json.loads(readin.text)['ip']
        print "Got external IP:", external_ip
        break
    except:
        print "Too many requests, trying again"
        sleepInterval = random.randint(10, 40)
        sleep(sleepInterval)


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
    
    game['blaster_id'] = external_ip
    game['referee_id'] = os.getpid()
    game['started'] = str(datetime.now())
    
    game['status'] = "Building"
    # make empty files for all the output files
    for prefix in [x['name'] for x in game['clients']]:
        for suffix in ['stdout', 'stderr', 'makeout', 'gitout']:
            with file('%s-%s.txt' % (prefix, suffix), 'w') as f:
                f.write('empty')
    
    # get latest client code in arena mode.
    # tournament mode will not fail games that clients fail to connect to
    for client in game['clients']:
        stalk.put(json.dumps(game))
        job.touch()
        if not update_local_repo(client):
            print "Failing the game, someone didn't clone"
            game['status'] = "Failed"
            game['completed'] = str(datetime.now())
            game['tied'] = False
            game['tie_reason'] = "The arena was unable to communicate with the webserver"
            push_datablocks(game)
            stalk.put(json.dumps(game))
            job.delete()
            return
      
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
    humans_be_here = False
    for i, cl in enumerate(game['clients']):
        print "Client", cl['name'], "is a", cl['language'], "client"
        if cl['language'] == 'Human':
            humans_be_here = True
            pla = subprocess.Popen(['bash',
                                  'arenaRun', game_name,
                                  '-r', game['number'],
                                  '-s', external_ip,
                                  '-i', str(i),
                                  '-n', cl['name'],
                                  '--chesser-master', 'r99acm.device.mst.edu:5454',
                                  '--printIO'
                                 ],
                                 stdout=subprocess.PIPE
                                 stderr=file('%s-stderr.txt' % cl['name'], 'w'),
                                 cwd=cl['name'])
        else:
            pla = subprocess.Popen(['bash',
                                  'arenaRun', game_name,
                                  '-r', game['number'],
                                  '-s', server_host,
                                  '-i', str(i),
                                  '-n', cl['name']
                                 ],
                                 stdout=subprocess.PIPE
                                 stderr=file('%s-stderr.txt' % cl['name'], 'w'),
                                 cwd=cl['name'])
        players.append(pla)
        limit = int(5e6)
        subprocess.Popen(['tail', '-c', str(limit)],
                        stdin=pla.stdout,
                        stdout=file('%s-stdout.txt' % cl['name'], 'w'))
    
    # make sure both clients have connected
    game_server_ip        = os.environ['SERVER_HOST']
    game_server_status    = requests.get('http://%s:3080/status/%s/%s' %
                            (game_server_ip, game_name, game['number'])).json()
    start_time            = int(round(time.time() * 1000))
    current_time          = start_time
    if not humans_be_here:
        MAX_TIME          = 10000           # in milliseconds
    else:
        MAX_TIME          = 2000000

    # block while at least one client is not connected
    while len(game_server_status['clients']) < 2 and (current_time - start_time <= MAX_TIME):
        if not humans_be_here:
            sleep(.01)     # wait a bit for the clients to connect
        else:
            job.touch()
            sleep(.1)
        current_time = int(round(time.time() * 1000))
        game_server_status = requests.get('http://%s:3080/status/%s/%s' %
                             (game_server_ip, game_name, game['number'])).json()

    
    # check if we timed out waiting for clients to connect
    if current_time - start_time > MAX_TIME:
        kill_clients(players)
        if game['origin'] != "Tournament":
            print "Failing the game, only %d clients connected" % (len(game_server_status['clients']))
            game['status'] = "Failed"
            game['complete'] = str(datetime.now())
            game['tied'] = False
            if len(game_server_status['clients']) == 0:
                game['tie_reason'] = "Game failed to start, neither client connected."
                game['clients'][0]['noconnect'] = True
                game['clients'][1]['noconnect'] = True
            elif len(game_server_status['clients']) == 1:
                for i, cl in enumerate(game['clients']):
                    if cl['name'] != game_server_status['clients'][0]['name']:
                        reason = ("Game failed to start,", cl['name'], "didn't connect.")
                        print cl['name'], "didn't connect"
                        game['tie_reason'] = ' '.join(reason)
                        game['clients'][i]['noconnect'] = True
        else:
            game['status'] = "Complete"
            game['complete'] = str(datetime.now())
            game['tied'] = False
            if len(game_server_status['clients']) == 0:
                randomWinner = random.randint(0,1)
                game['winner'] = game['clients'][randomWinner]
                if randomWinner == 0:
                    game['loser'] = game['clients'][1]
                else:
                    game['loser'] = game['clients'][0]
                reason = ("Neither client connected, so", game['clients'][randomWinner]['name'], "wins by coin flip.")
                game['win_reason'] = ' '.join(reason)
                game['lose_reason'] = ' '.join(reason)
                print reason
            elif len(game_server_status['clients']) == 1:
                for i, cl in enumerate(game['clients']):
                    if cl['name'] != game_server_status['clients'][0]['name']:
                        game['loser'] = cl
                        if cl['name'] == game['clients'][0]['name']:
                            game['winner'] = game['clients'][1]
                            reason = (cl['name'], "didn't connect.")
                            game['win_reason'] = ' '.join(reason)
                            game['lose_reason'] = ' '.join(reason)
                        else:
                            game['winner'] = game['clients'][0]
                            reason = (cl['name'], "didn't connect.")
                            game['win_reason'] = ' '.join(reason)
                            game['lose_reason'] = ' '.join(reason)
	push_datablocks(game)
	stalk.put(json.dumps(game))
	job.delete()
        return
    
    # game is running. 
    print "Running...", game['number']
    server_path = os.environ['SERVER_PATH']
    game['status'] = "Running"
    stalk.put(json.dumps(game))

    
    # wait until the game is over
    game_server_status = requests.get('http://%s:3080/status/%s/%s' %
                         (game_server_ip, game_name, game['number'])).json()
    start_time            = int(round(time.time() * 1000))
    current_time          = start_time
    MAX_TIME              = 2500000
    
    while game_server_status['status'] == 'running' and current_time - start_time <= MAX_TIME:
        job.touch()
        sleep(0.1)
        current_time = int(round(time.time() * 1000))
        game_server_status = requests.get('http://%s:3080/status/%s/%s' %
                             (game_server_ip, game_name, game['number'])).json()
	
	
    if current_time - start_time > MAX_TIME:
        kill_clients(players)
        print "Failing game, took to long"
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
    
    if 'disconnected' in game_server_status['clients'][0]:
        if game_server_status['clients'][0]['disconnected']:
            p0broke = True
            print game_server_status['clients'][0]['name'], "disconnected"
        else:
            p0broke = False
    else:
        p0broke = False
    if 'disconnected' in game_server_status['clients'][1]:
        if game_server_status['clients'][1]['disconnected']:
            p1broke = True
            print game_server_status['clients'][1]['name'], "disconnected"
        else:
            p1broke = False
    else:
        p1broke = False


    if p0broke or p1broke:
        #print "game %s early termination, broken client" % game['number']
        #game['status'] = "Failed"
        #game['completed'] = str(datetime.now())
        #game['tied'] = False
        if p0broke:
            game['clients'][0]['discon'] = True
            #reason = ("Early termination because", game_server_status['clients'][0]['name'], "disconnected unexpectedly.")
            #game['tie_reason'] = ' '.join(reason)
        if p1broke:
            game['clients'][1]['discon'] = True
            #reason = ("Early termination because", game_server_status['clients'][1]['name'], "disconnected unexpectedly.")
            #game['tie_reason'] = ' '.join(reason)
        """
        push_datablocks(game)
        try:
            push_gamelog(game)
        except:
            pass
        stalk.put(json.dumps(game))
        job.delete()
        return
        """
    # figure out who won
    print "determining winner..."
    if ('won' in game_server_status['clients'][0] and 'won' in game_server_status['clients'][1]) or ('lost' in game_server_status['clients'][0] and 'lost' in game_server_status['clients'][1]):
        game['tied'] = True
        game['tie_reason'] = game_server_status['clients'][0]['reason']
        print game['clients'][0]['name'], "and", \
            game['clients'][1]['name'], "tied!"
    else:
        game['tied'] = False
        if 'won' in game_server_status['clients'][0]:
            game['winner'] = game['clients'][0]
            game['loser'] = game['clients'][1]
            game['win_reason'] = game_server_status['clients'][0]['reason']
            game['lose_reason'] = game_server_status['clients'][1]['reason']
        else:
            game['winner'] = game['clients'][1]
            game['loser'] = game['clients'][0]
            game['win_reason'] = game_server_status['clients'][1]['reason']
            game['lose_reason'] = game_server_status['clients'][0]['reason']
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
	    subprocess.call(['kill', '-15', str(x.pid)])
	except OSError as e:
	    print "it didn't dieeee!!!", e
	    pass


def compile_client(client):
    ''' Compile the client and return the code returned by make '''
    print 'Making %s/%s' % (os.getcwd(), client['name'])
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
        try:
            k.set_contents_from_filename(local_filename, {'Content-Type': 'application/json; charset=utf-8', 'Content-Encoding': 'gzip', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Origin,X-Requested-With,Content-Type,Accept'}, policy='public-read')
        except:
            sleep(5)
            k.set_contents_from_filename(local_filename, {'Content-Type': 'application/json; charset=utf-8', 'Content-Encoding': 'gzip', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Origin,X-Requested-With,Content-Type,Accept'}, policy='public-read')
    else:
        k.set_contents_from_filename(local_filename, policy='public-read')
    return "http://%s.s3.amazonaws.com/%s" % (bucket_name, k.key)


def push_datablocks(game):
    ''' Make zip files containing client data and push them to s3 '''
    for client in game['clients']:
        in_name = "%s-data.zip" % client['name']
        with zipfile.ZipFile(in_name, 'w', zipfile.ZIP_DEFLATED, allowZip64 = True) as z:
            for suffix in ['stdout', 'stderr', 'makeout', 'gitout']:
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
    game['gamelog_url'] = push_file(gamelog_filename, remote, True)
    os.remove(gamelog_filename)


def update_local_repo(client):
    '''Get the appropriate code and version from the repository'''
    base_path = os.environ['CLIENT_PREFIX']
    subprocess.call(['rm', '-rf', client['name']],
                    stdout=file('/dev/null'),
                    stderr=subprocess.STDOUT)
    
    numFailed = 0
    while numFailed < 750:        #try to clone 750 times, should come out just shy of 400 seconds
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
    if numFailed >= 750:
        return False
    
    subprocess.call(['git', 'pull'], cwd=client['name'],
                    stdout=file('%s-gitout.txt' % client['name'], 'a'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'checkout', client['tag']],
                    stdout=file('%s-gitout.txt' % client['name'], 'a'),
                    stderr=subprocess.STDOUT,
                    cwd=client['name'])
    print "Checking out ", client['tag']
    return True

if __name__ == "__main__":
    main()
