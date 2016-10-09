#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import re
import json
import subprocess
import os
import signal
import random
import socket
import fcntl
import struct
import md5
import zipfile
from time import sleep
from datetime import datetime
from bz2 import BZ2File

# Non-Django 3rd Party Imports
import beanstalkc
import boto


def get_interface_ip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])

def public_ip():    
    ec2conn = boto.connect_ec2(os.environ['ACCESS_CRED'], os.environ['SECRET_CRED'])
    reservations = ec2conn.get_all_instances()
    instances = [i for r in reservations for i in r.instances]

    possible_ips = [["eth0", None], ["eth1", None]]
    for i in possible_ips:
        try:
            i[1] = get_interface_ip(i[0])
        except:
            pass

    public_ip_address = None
    print possible_ips    
    for i in instances:
        for j in possible_ips:
            print j, i.private_ip_address
            if str(i.private_ip_address) == str(j[1]) and j[1] is not None:
                print "setting public ip address"
                public_ip_address = i.ip_address     
        
    if public_ip_address is not None:
        return public_ip_address
    else:
        return possible_ips[0][1]

public_ip_address = public_ip() #hopefully
# public_ip_address = "192.168.1.7"
print "MY ip address is", public_ip_address

def main():
    stalk = beanstalkc.Connection(host=os.environ['BEANSTALK_HOST'])
    stalk.watch('game-requests-%s' % os.environ['GAME_NAME'])  # input
    stalk.use('game-results-%s' % os.environ['GAME_NAME'])     # output
    while True:
        looping(stalk)

def touch_job(job):
    try:
        job.touch()
    except beanstalkc.CommandFailed:
        return True
    return False

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
    if touch_job(job):
        return
    for client in game['clients']:
        client['compiled'] = (compile_client(client) is 0)
        if touch_job(job):
            return
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

    # special stuff for human clients
    p0_human = 'Human' in game['clients'][0]['language']
    p1_human = 'Human' in game['clients'][1]['language']
    
    #ports for human players
    human_port_p0 = "18003"
    m_port_p0 = "18010"
    human_port_p1 = "18006"
    m_port_p1 = "18011"
    if p0_human:
        print "Player 1 is Human"
        tunneler0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tunneler0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tunneler0.bind(('localhost', int(human_port_p0)))
        game_start_pat = ""
    if p1_human:
        print "Player 2 is Human"
        tunneler1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tunneler1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tunneler1.bind(('localhost', int(human_port_p1)))
    if not (p0_human or p1_human):
        print "no human"
    # start the clients
    server_host = os.environ['SERVER_HOST']
    players = list()
    print "Humans, p0", p0_human, "p1", p1_human
    for index, cl in enumerate(game['clients']):
        print "Index", index
        if index == 0:
            pla = subprocess.Popen(['bash', 'run', server_host, game['number'], m_port_p0, human_port_p0],
                                    stdout=subprocess.PIPE,
                                    stderr=file('%s-stderr.txt' % cl['name'], 'w'),
                                    cwd=cl['name'])

        if index == 1:
            pla = subprocess.Popen(['bash', 'run', server_host, game['number'], m_port_p1, human_port_p1],
                                    stdout=subprocess.PIPE,
                                    stderr=file('%s-stderr.txt' % cl['name'], 'w'),
                                    cwd=cl['name'])
        players.append(pla)
        limit = int(5e6)
        subprocess.Popen(['tail', '-c', str(limit)],
                        stdin=pla.stdout,
                        stdout=file('%s-stdout.txt' % cl['name'], 'w'))

        if p0_human and index == 0:
            # listen for tunneler
            game['clients'][index]['game_ready'] = True
            game['clients'][index]['game_location'] = public_ip_address
            game['clients'][index]['game_number'] = game['number']        
            game['clients'][index]['game_port'] = m_port_p0
            stalk.put(json.dumps(game))
            job.touch()
            print "waiting for tunneler"

            tunneler0.listen(1)
            tunn0_conn, tunn0_addr = tunneler0.accept()
            
            print "Waiting for human client 1"
            job.touch()
            try:
                data = tunn0_conn.recv(10000)
            except socket.timeout:
                data = None
            if data is not None:
                print 'data', data                    
            
            game['clients'][0]['game_ready'] = 'In Action'
            stalk.put(json.dumps(game))
            job.touch()
            tunneler0.close()

        if p1_human and index == 1:
            game['clients'][1]['game_ready'] = True
            game['clients'][1]['game_location'] = public_ip_address
            game['clients'][1]['game_number'] = game['number']
            game['clients'][index]['game_port'] = m_port_p1
            stalk.put(json.dumps(game))
            job.touch()
            
            tunneler1.listen(1)
            tunn1_conn, tunn1_addr = tunneler1.accept()
            job.touch()
            try:
                data = tunn1_conn.recv(10000)
            except socket.timeout:
                data = None
            if data is not None:
                print 'data', data
            game['clients'][0]['game_ready'] = 'In Action'
            stalk.put(json.dumps(game))
            job.touch()
            tunneler1.close()
        sleep(10)
    #make sure beanstalk doesn't rest game
    if touch_job(job):
        return

    stalk.put(json.dumps(game))
    job.touch()

    #for cl in game['clients']:
    #    sleep(10)  # ensures ['clients'][0] plays as p0
    #    players.append(
    #        subprocess.Popen(['bash', 'run', server_host, game['number']],
    #                         stdout=file('%s-stdout.txt' % cl['name'], 'w'),
    #                         stderr=file('%s-stderr.txt' % cl['name'], 'w'),
    #                         cwd=cl['name']))

    # game is running. watch for gamelog

    print "running...", game['number']
    server_path = os.environ['SERVER_PATH']
    game['status'] = "Running"
    stalk.put(json.dumps(game))
    p0_good = True
    p1_good = True
    p0_exit = None
    p1_exit = None
    glog_done = False
    while p0_good and p1_good and not glog_done:
        job.touch()
        sleep(5)
        # p0_exit = players[0].poll()
        # p1_exit = players[1].poll()

        p0_good = players[0].poll() is None
        p1_good = players[1].poll() is None
        glog_done = os.access("%s/logs/%s.glog" %
                              (server_path, game['number']), os.F_OK)

    for x in players:
      if x.poll() is None:
        print "*************************************** die", x.pid
        x.kill() 
      #try:
      #  print "*************************************** die", x.pid
        #os.killpg(x.pid, signal.SIGTERM)
      #  subprocess.call(['kill', '-9', str(x.pid)], cwd=client['name'],
      #              stdout=file("/dev/null", "w"),
      #              stderr=subprocess.STDOUT)
      #except OSError as e:
      #  print "it didn't dieeee!!!", e

    job.touch()

    game['clients'][0]['game_ready'] = False
    game['clients'][1]['game_ready'] = False

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
    f = BZ2File("%s/logs/%s.glog" % (server_path, game_number), 'r')
    log = f.read()
    #print log
    f.close()
    match = re.search("\"game-winner\" (\d+) \"[^\"]+\" (\d+)", log)
    if match:
        return match.groups()[1]
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
    k.key = remote_filename
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
    gamelog_filename = "%s/logs/%s.glog" % (server_path, game['number'])
    # salt exists to stop people from randomly probing for files
    salt = md5.md5(str(random.random())).hexdigest()[:5]
    remote = "%s-%s.glog" % (game['number'], salt)
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
