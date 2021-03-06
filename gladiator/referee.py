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
import sys
import shutil
import multiprocessing
from time import sleep
from datetime import datetime 

# Non-Django 3rd Party Imports
import beanstalkc
import boto


game_name = os.environ['GAME_NAME']
mode = os.environ['MODE']

print "Playing with game slug: ", game_name

while True:
    print "Getting external IP"
    try:
        #url = 'http://ifconfig.co'
        #headers = {'Accept': 'application/json'}
        #readin = requests.get(url, headers=headers, timeout=10)
        #external_ip = json.loads(readin.text)['ip']
        external_ip = 'arena.siggame.io'
        print "Got external IP:", external_ip
        break
    except:
        print "Too many requests, trying again"
        sleepInterval = random.randint(10, 60)
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
    i0 = False
    i1 = False
    for i, client in enumerate(game['clients']):
        stalk.put(json.dumps(game))
        job.touch()
        if not update_local_repo(client, game['timeout'], job, game['persistent']):
            print "Failing the game, someone didn't download"
            game['status'] = "Failed"
            game['completed'] = str(datetime.now())
            game['tied'] = False
            game['tie_reason'] = "The arena was unable to communicate with the webserver"
            push_datablocks(game)
            stalk.put(json.dumps(game))
            job.delete()
            return
        subprocess.call(['mkdir', 'arenaupload/'], cwd=client['name'])
    
    # compile the clients
    stalk.put(json.dumps(game))
    job.touch()
    
    # fail the game if someone didn't compile in arena mode.
    # tournament mode absolutely cannot have failed games.
    # ties are ok, but really annoying

    for i, client in enumerate(game['clients']):
        if i == 0:
            compileProcess0 = multiprocessing.Process(target=compile_client, args=(client,))
            compileProcess0.start()
        else:
            compileProcess1 = multiprocessing.Process(target=compile_client, args=(client,))
            compileProcess1.start()

    compileProcess0.join()
    job.touch()
    compileProcess1.join()
    job.touch()
    
    for i, client in enumerate(game['clients']):
        if i == 0:
            client['compiled'] = (compileProcess0.exitcode is 0)
            print "result for make in %s was %s" % (client['name'], client['compiled'])
        else:
            client['compiled'] = (compileProcess1.exitcode is 0)
            print "result for make in %s was %s" % (client['name'], client['compiled'])
        if not client['compiled']:
            if game['origin'] != "Tournament": 
                print "Failing the game, someone didn't compile"
                game['status'] = "Failed"
                game['completed'] = str(datetime.now())
                game['tied'] = False
                game['tie_reason'] = "%s didn't compile" % client['name']
                push_datablocks(game)
                stalk.put(json.dumps(game))
                job.delete()
                return
            else:
                print client['name'], "didn't compile (lame)"
                game['status'] = "Complete"
                game['completed'] = str(datetime.now())
                game['tied'] = False
                if client['name'] == game['clients'][0]:
                    game['winner'] = game['clients'][1]
                    game['loser'] = game['clients'][0]
                else:
                    game['winner'] = game['clients'][0]
                    game['loser'] = game['clients'][1]
                reason = (client['name'], "didn't compile (lame).")
                game['win_reason'] = ' '.join(reason)
                game['lose_reason'] = ' '.join(reason)
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
                                  '-p', os.environ['WEB_CLIENT_PORT'],
                                  '-i', str(i),
                                  '-n', cl['name'],
                                  '--chesser-master', 'r99acm.device.mst.edu:5454',
                                  '--printIO'
                                 ],
                                 stdout=subprocess.PIPE,
                                 stderr=file('%s-stderr.txt' % cl['name'], 'w'),
                                 cwd=cl['name'])
        else:
            pla = subprocess.Popen(['bash',
                                  'run', game_name,
                                  '-r', game['number'],
                                  '-s', server_host,
                                  '-p', os.environ['CLIENT_PORT'],
                                  '-i', str(i),
                                  '-n', cl['name']
                                 ],
                                 stdout=subprocess.PIPE,
                                 stderr=file('%s-stderr.txt' % cl['name'], 'w'),
                                 cwd=cl['name'])
        players.append(pla)
        limit = 5242880 #5MB
        subprocess.Popen(['tail', '-c', str(limit)],
                        stdin=pla.stdout,
                        stdout=file('%s-stdout.txt' % cl['name'], 'w'))
    
    # make sure both clients have connected
    game_server_ip        = os.environ['SERVER_HOST']
    game_server_status    = requests.get('http://%s:%s/status/%s/%s' %
                            (game_server_ip, os.environ['API_PORT'], game_name, game['number'])).json()
    start_time            = int(round(time.time() * 1000))
    current_time          = start_time
    if not humans_be_here:
        MAX_TIME          = 10000           # in milliseconds
    else:
        MAX_TIME          = 1000000

    # block while at least one client is not connected
    while len(game_server_status['clients']) < 2 and (current_time - start_time <= MAX_TIME):
        if not humans_be_here:
            sleep(.01)     # wait a bit for the clients to connect
        else:
            job.touch()
            sleep(.1)
        current_time = int(round(time.time() * 1000))
        game_server_status = requests.get('http://%s:%s/status/%s/%s' %
                             (game_server_ip, os.environ['API_PORT'], game_name, game['number'])).json()

    
    # check if we timed out waiting for clients to connect
    if current_time - start_time > MAX_TIME:
        killDaPlayers = multiprocessing.Process(target=kill_clients, args=(players,))
        killDaPlayers.start()
        if game['origin'] != "Tournament":
            print "Failing the game, only %d clients connected" % (len(game_server_status['clients']))
            game['status'] = "Failed"
            game['completed'] = str(datetime.now())
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
            game['completed'] = str(datetime.now())
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
    game_server_status = requests.get('http://%s:%s/status/%s/%s' %
                         (game_server_ip, os.environ['API_PORT'], game_name, game['number'])).json()
    start_time            = int(round(time.time() * 1000))
    current_time          = start_time
    MAX_TIME              = 2500000
    
    while game_server_status['status'] == 'running' and current_time - start_time <= MAX_TIME:
        job.touch()
        sleep(0.1)
        current_time = int(round(time.time() * 1000))
        game_server_status = requests.get('http://%s:%s/status/%s/%s' %
                             (game_server_ip, os.environ['API_PORT'], game_name, game['number'])).json()
	
    killDaPlayers = multiprocessing.Process(target=kill_clients, args=(players,))
    killDaPlayers.start()
        
    if current_time - start_time > MAX_TIME:
        print "Failing game, took too long"
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
    
    game_server_status = requests.get('http://%s:%s/status/%s/%s' %
                         (game_server_ip, os.environ['API_PORT'], game_name, game['number'])).json()
    
    while game_server_status['gamelogFilename'] is None:
        game_server_status = requests.get('http://%s:%s/status/%s/%s' %
                             (game_server_ip, os.environ['API_PORT'], game_name, game['number'])).json()
        sleep(0.25)
    game_server_status = requests.get('http://%s:%s/status/%s/%s' %
                         (game_server_ip, os.environ['API_PORT'], game_name, game['number'])).json()

    glog_location = game_server_status['gamelogFilename']
    
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
        if p0broke:
            game['clients'][0]['discon'] = True
        if p1broke:
            game['clients'][1]['discon'] = True
            
    # figure out who won
    print "determining winner..."
    if (game_server_status['clients'][0]['won'] is True and game_server_status['clients'][1]['won'] is True) or (game_server_status['clients'][0]['won'] is False and game_server_status['clients'][1]['won'] is False):
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
    push_gamelog(game, glog_location)
    game['status'] = "Complete"
    game['completed'] = str(datetime.now())
    stalk.put(json.dumps(game))
    job.delete()
    print "%s done %s" % (game['number'], str(datetime.now()))
    return


def kill_clients(players):
    sleep(40)
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
    subprocess.call(['make', 'clean'], cwd=client['name'])
    exit(subprocess.call(['make'], cwd=client['name'],
                           stdout=file("%s-makeout.txt" % client['name'], "w"),
                           stderr=subprocess.STDOUT))


def push_file(local_filename, remote_filename, is_glog, game=None):
    ''' Push this thing to s3
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
    return "http://%s.s3.amazonaws.com/%s" % (bucket_name, k.key)'''
    if is_glog:
        f = open(local_filename, 'r')
        glog = f.read()
        f.close()
        game['glog_name'] = remote_filename
        game['gamelog'] = glog
    else:
        return "None"
    

def push_datablocks(game):
    ''' Make zip files containing client data and push them to s3 '''
    Size = 0
    for client in game['clients']:
        in_name = "%s-data.zip" % client['name']
        theirStuff = './%s/arenaupload/' % client['name']
        theirStuffName = 'yourstuff.zip'
        maxSize = 314572800
        tooBig = False
        with zipfile.ZipFile(theirStuffName, 'w', zipfile.ZIP_DEFLATED, allowZip64 = True) as y:
            for root, dirs, files in os.walk(theirStuff):
                for file in files:
                    y.write(os.path.join(root, file))
        if os.path.getsize('./%s' % theirStuffName) > maxSize:
            os.remove(theirStuffName)
            with open('toobig.txt', 'w') as x:
                x.write('The contents of your arenaupload folder exceeded %s bytes.' % maxSize)
            tooBig = True
            print "%s tried to upload too much" % client['name']
        else:
            tooBig = False
        with zipfile.ZipFile(in_name, 'w', zipfile.ZIP_DEFLATED, allowZip64 = True) as z:
            for suffix in ['stdout', 'stderr', 'makeout', 'gitout']:
                z.write('%s-%s.txt' % (client['name'], suffix))
            if tooBig:
                z.write('toobig.txt')
            else:
                z.write(theirStuffName)
        try:
            os.remove(theirStuffName)
        except:
            pass
        try:
            shutil.rmtree(theirStuff)
        except:
            pass
        salt = md5.md5(str(random.random())).hexdigest()[:5]
        remote = "%s-%s-%s-data.zip" % (game['number'], salt, client['name'])
        client['output_url'] = push_file(in_name, remote, False)
        os.remove(in_name)


def push_gamelog(game, glog_location):
    '''Push gamelog to S3'''
    server_path = os.environ['SERVER_PATH']
    gamelog_filename_zipped = "%s/logs/gamelogs/%s.json.gz" % (server_path, glog_location)
    subprocess.call(['gunzip', gamelog_filename_zipped], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    gamelog_filename = "%s/logs/gamelogs/%s.json" % (server_path, glog_location)
    # salt exists to stop people from randomly probing for files
    salt = md5.md5(str(random.random())).hexdigest()[:5]
    remote = "%s-%s.json" % (glog_location, salt)
    push_file(gamelog_filename, remote, True, game)
    os.remove(gamelog_filename)


def update_local_repo(client, timeout, job, persistent):
    '''Get the appropriate code and version from the repository'''
    base_path = os.environ['CLIENT_PREFIX']
    subprocess.call(['rm', '-rf', client['name']],
                    stdout=file('/dev/null'),
                    stderr=subprocess.STDOUT)
    if not persistent or not os.path.isdir('./%s' % client['name']):
        numFailed = 0
        max_tries = int(round(timeout / 4))
        while numFailed < max_tries:        #try to download max_tries times
            if numFailed != 0:
                sys.stderr.write('Download failed %s times\n' % numFailed)
            #try:
            if True:
                if mode == 'git':
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
                elif mode == 'file':
                    print "wget %s:80/gladiator/%s.zip client: %s" % (os.environ['BEANSTALK_HOST'], client['name'], client['name'])
                    #Cleanup any leftover files before beginning
                    subprocess.call(['rm', '-rf', client['repo'], '%s.zip*' % (client['name'])],
                                    stdout=file('%s-gitout.txt' % client['name'], 'w'),
                                    stderr=subprocess.STDOUT)
                    #Download client zip from head node
                    subprocess.call(['wget', '%s:80/gladiator/%s.zip' % (os.environ['BEANSTALK_HOST'], client['name'])],
                                    stdout=file('%s-gitout.txt' % client['name'], 'w'),
                                    stderr=subprocess.STDOUT)
                    #Unzip client
                    '''
                    subprocess.call(['unzip', '-o', '%s.zip' % (client['name'])],
                                    stdout=file('%s-gitout.txt' % client['name'], 'w'),
                                    stderr=subprocess.STDOUT)
                    '''
                    with zipfile.ZipFile('%s.zip' % (client['name']), 'r') as zip_ref:
                        zip_ref.extractall('client')
                    #Make client directory
                    #subprocess.call(['mkdir', client['name']],
                    #                stdout=file('%s-gitout.txt' % client['name'], 'w'),
                    #                stderr=subprocess.STDOUT)
                    path = os.path.dirname(__file__) + client['name']
                    os.mkdir(path)
                    #Move client files into client directory
                    #print 'mv', '%s/*' % (client['repo']), client['name']
                    #subprocess.call(['mv', '%s/*' % (client['repo']), client['name']],
                    #                stdout=file('%s-gitout.txt' % client['name'], 'w'),
                    #                stderr=subprocess.STDOUT)
                    print "Check folder deepness"
                    if 'run' in os.listdir(os.path.dirname(__file__) + 'client' + '/'):
                        print "0 Deep"
                        print os.listdir(os.path.dirname(__file__) + 'client' + '/')
                        #source = str(os.listdir(os.path.dirname(__file__) + 'client' + '/'))
                        source = ""
                    elif 'run' in os.listdir(os.path.dirname(__file__) + 'client' + '/' + str(os.listdir(os.path.dirname(__file__) + 'client' + '/')[0]) + '/'):
                        print "1 Deep"
                        print os.listdir(os.path.dirname(__file__) + 'client' + '/' + str(os.listdir(os.path.dirname(__file__) + 'client' + '/')[0]) + '/')
                        #source = str(os.listdir(os.path.dirname(__file__) + 'client' + '/' + str(os.listdir(os.path.dirname(__file__) + 'client' + '/')[0]) + '/')[0])[2:-2] + '/'
                        source = str(os.listdir(os.path.dirname(__file__) + 'client' + '/')[0]) + '/'
                    else:
                        print "2 or more Deep"
                        print os.listdir(os.path.dirname(__file__) + 'client' + '/' + str(os.listdir(os.path.dirname(__file__) + 'client' + '/')[0]) + '/') + os.listdir(os.path.dirname(__file__) + 'client' + '/' + os.listdir(os.path.dirname(__file__) + 'client' + '/')[0] + '/')
                        #source = str((os.listdir(os.path.dirname(__file__) + 'client' + '/' + str(os.listdir(os.path.dirname(__file__) + 'client' + '/')[0]) + '/') + str(os.listdir(os.path.dirname(__file__) + 'client' + '/' + str(os.listdir(os.path.dirname(__file__) + 'client' + '/')[0]) + '/'))[0]))[2:-2] + '/'
                        source = str(os.listdir(os.path.dirname(__file__) + 'client' + '/' + str(os.listdir(os.path.dirname(__file__) + 'client' + '/')[0]) + '/')[0]) + '/'
                    source = 'client/' + source
                    dest = os.path.dirname(__file__) + client['name']
                    files = os.listdir(source)
                    for f in files:
                        shutil.move(source+f, dest+'/')
                    #Cleanup
                    subprocess.call(['rm', '-rf', client['repo'], '%s.zip' % (client['name']), 'client'],
                                    stdout=file('%s-gitout.txt' % client['name'], 'w'),
                                    stderr=subprocess.STDOUT)
                    print "Download successful!"
                    break
                else:
                    assert(False), "Invalid mode"
            '''
            except OSError:
                numFailed += 1      #keep track of how many times
                print "Download failed, retrying"
                if numFailed <= 15:
                    sleep(0.01)         #Wait 10ms before attempting to clone again
                elif numFailed > 15:
                    sleep(.5)
            '''
            job.touch()
        if numFailed >= max_tries:
            return False

    if mode == 'git':
        subprocess.call(['git', 'pull'], cwd=client['name'],
                        stdout=file('%s-gitout.txt' % client['name'], 'a'),
                        stderr=subprocess.STDOUT)
        subprocess.call(['git', 'checkout', client['hash']],
                        stdout=file('%s-gitout.txt' % client['name'], 'a'),
                        stderr=subprocess.STDOUT,
                        cwd=client['name'])
        print "Checking out ", client['hash']
    return True

if __name__ == "__main__":
    main()
