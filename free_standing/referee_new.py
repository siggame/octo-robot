#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# referee no longer allowed to touch database
# pipes only!

# os.environ['CLIENT_PREFIX']
# os.environ['SERVER_PATH']
# os.environ['SERVER_HOST']
# os.environ['GAME_NAME']
# os.environ['S3_PREFIX']
# os.environ['ACCESS_CRED']
# os.environ['SECRET_CRED']
# os.environ['BEANSTALK_HOST']

from datetime import datetime

# 3rd Party Imports
import re, json               # special strings
import beanstalkc, boto       # networky
import subprocess, os         # shellish
import random, time

stalk = None

def main():
    global stalk
    stalk = beanstalkc.Connection(host=os.environ['BEANSTALK_HOST'])    
    stalk.watch('game-requests-%s' % os.environ['GAME_NAME']) # input
    stalk.use('game-results-%s'    % os.environ['GAME_NAME']) # output
    while True:
        looping()
        
        
def looping():
    '''Get a game, process it, repeat'''
    job = stalk.reserve()
    game = json.loads(job.body)
    print "processing game", game['number']
    
    for client in game['clients']:
        update_local_repo(client)
        
    # make empty files for all the output files
    for prefix in [x['name'] for x in game['clients']]:
        for suffix in ['stdout', 'stderr', 'makeout', 'gitout']:
            with file('%s-%s.txt' % (prefix, suffix), 'w') as f:
                f.write('empty')
    
    # get and compile the clients
    game['status'] = "Building"
    stalk.put(json.dumps(game))
    for client in game['clients']:
        client['compiled'] = (compile_client(client) is 0)
        job.touch()
        print "result for make in %s was %s" % (client['name'], 
                                                client['compiled'])

    # handle a failed game
    if not all([x['compiled'] for x in game['clients']]):
        print "failing the game, someone didn't compile"
        game['status'] = "Failed"
        game['completed'] = str(datetime.now())
        stalk.put(json.dumps(game))
        push_datablocks(game)
        job.delete()
        return
    
    # start the clients
    server_host = os.environ['SERVER_HOST']
    players = list()
    for cl in game['clients']:
        time.sleep(5)
        players.append(
            subprocess.Popen(['bash', 'run', server_host, game['number']], 
                             stdout=file('%s-stdout.txt' % cl['name'], 'w'),
                             stderr=file('%s-stderr.txt' % cl['name'], 'w'),
                             cwd=cl['name']))
    

    # FIXME if .poll() is not None then a process has ended
    #       this indicates that it has blown up 
    #       before connecting to the server
    
    # game is running. watch for gamelog
    print "running..."
    server_path = os.environ['SERVER_PATH']
    game['status'] = "Running"
    stalk.put(json.dumps(game))
    while not os.access("%s/logs/%s.glog" % (server_path, game['number']), 
                        os.F_OK):
        job.touch()
        time.sleep(10)
    
    # figure out who won by reading the gamelog
    print "determining winner..."
    winner = parse_gamelog(game['number'])
    if winner == '0':
        game['winner'] = game['clients'][0]
        game['loser']  = game['clients'][1]
    elif winner == '1':
        game['winner'] = game['clients'][0]
        game['loser']  = game['clients'][1]
    elif winner == '2':
        game['tied'] = True
    
    # clean up
    print "cleaning up..."
    [x.terminate() for x in players]
    print "pushing gamelog..."
    push_gamelog(game)
    print "pushing data blocks..."
    push_datablocks(game)
    game['status'] = "Complete"
    game['completed'] = str(datetime.now())
    stalk.put(json.dumps(game))
    job.delete()
    print "%s done %s" % (game['number'], str(datetime.now()))

    
def compile_client(client):
    ''' Compile the client and return the code returned by make '''
    subprocess.call(['make', 'clean'], cwd=client['name'],
                    stdout=file("/dev/null", "w"),
                    stderr=subprocess.STDOUT)
    return subprocess.call(['make'], cwd=client['name'],
                           stdout=file("%s-makeout.txt" % client['name'], "w"),
                           stderr=subprocess.STDOUT)


from bz2 import BZ2File
def parse_gamelog(game_number):
    ''' Determine winner by parsing that last s-expression in the gamelog
        the gamelog is now compressed. '''
    server_path = os.environ['SERVER_PATH']
    f = BZ2File("%s/logs/%s.glog" % (server_path, game_number), 'r')
    log = f.readline()
    f.close()
    match = re.search("\"game-winner\" (\d+) \"[^\"]+\" (\d+)", log)
    if match:
        return match.groups()[1]
    return None


def push_file( local_filename, remote_filename ):
    ''' Push this thing to s3 '''
    bucket_name = "%s-%s" % (os.environ['S3_PREFIX'], os.environ['GAME_NAME'])
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
    ''' Make zip files containing client data and push them to s3 '''
    for client in game['clients']:
        in_name = "%s-data.zip" % client['name']
        with zipfile.ZipFile(in_name, 'w', zipfile.ZIP_DEFLATED) as z:
            #for suffix in ['stdout', 'stderr', 'makeout', 'gitout']:
            for suffix in ['makeout', 'gitout']:
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
    subprocess.call(['git', 'checkout', client['current_version']],
                    stdout=file('%s-gitout.txt' % client['name'], 'a'),
                    stderr=subprocess.STDOUT,
                    cwd=client['name'])

main()
