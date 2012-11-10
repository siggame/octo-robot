#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

'''Fake ref doesn't actually run games'''
# game['fake_ref'] = True  will always be returned

# game['broken_test'] = ['client_name', 'another_client_name']
# These clients will fail to build

# game['runtime_test'] = 15
# This game will take 15 seconds to run

# game['no_glog_test'] exists
# This game status will be failed, and will be looking for...
# game['p0_broken_test'] exists -> p0 is broken
# game['p1_broken_test'] exists -> p1 is broken

# game['declared_winner_test'] = '1' -> p1 will be declared winner
# game['ties_ok_test'] exists then random.choice(['0','1','2']) is winner
# else random.choice(['0','1']) is winner


from datetime import datetime
import json                   # special strings
import beanstalkc             # networky
import os                     # shellish
import random, time
import socket

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

    game['blaster_id'] = socket.gethostname()
    game['referee_id'] = os.getpid()
    game['started'] = str(datetime.now())
    game['fake_ref'] = True

    # fake ref doesn't care about client code
    # compile the clients
    game['status'] = "Building"
    stalk.put(json.dumps(game))
    job.touch()
    
    # if the game request asks, then fake_ref will pretend like
    # that client code failed to compile
    for client in game['clients']:
        client['compiled'] = True
    if 'broken_test' in game:
        for client in game['clients']:
            if client in game['broken_test']:
                client['compiled'] = False
                print "claiming %s did not compile" % client['name']
    
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
    
    # game is "running"
    print "running..."
    game['status'] = "Running"
    stalk.put(json.dumps(game))

    if 'runtime_test' in game: # pause a bit if requested
        time.sleep(game['runtime_test'])

    print "pushing data blocks..."
    push_datablocks(game)
    
    if 'no_glog_test' in game:
        game['status'] = "Failed"
        game['completed'] = str(datetime.now())
        if 'p0_broken_test' in game:
            game['clients'][0]['broken'] = True
        if 'p1_broken_test' in game:
            game['clients'][0]['broken'] = True
        stalk.put(json.dumps(game))
        job.delete()
        return

    # figure out who won by reading the gamelog
    print "determining winner..."
    winner = parse_gamelog(game)
    if winner == '2':
        game['tied'] = True
        print game['clients'][0]['name'], "and", game['clients'][1]['name'], "tied!"
    else:
        if winner == '0':
            game['winner'] = game['clients'][0]
            game['loser']  = game['clients'][1]
        elif winner == '1':
            game['winner'] = game['clients'][1]
            game['loser']  = game['clients'][0]
        print game['winner']['name'], "beat", game['loser']['name']
    
    # clean up
    print "pushing gamelog..."
    push_gamelog(game)
    game['status'] = "Complete"
    game['completed'] = str(datetime.now())
    stalk.put(json.dumps(game))
    job.delete()
    print "%s done %s" % (game['number'], str(datetime.now()))


def parse_gamelog(game):
    if 'declared_winner_test' in game:
        return game['declared_winner_test']
    if 'ties_ok_test' in game:
        return random.choice(['0', '1', '2'])
    return random.choice(['0', '1'])
    

def push_datablocks(game):
    for client in game['clients']:
        client['output_url'] = "http://nothing"
        

def push_gamelog(game):
    game['gamelog_url'] = "http://nothing"


    
if __name__ == "__main__":
    main()
