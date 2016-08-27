#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####


# Standard Imports
import time
import urllib
import math
import gzip
import os
import urllib2
from copy import copy
from multiprocessing import Process
from datetime import datetime, timedelta
from bz2 import BZ2Decompressor
from collections import defaultdict

# Non-Django 3rd Party Imports
import json

# My Imports
from thunderdome.config import game_name
from thunderdome.models import Client, Game, GameData, Referee, GameStats
from thunderdome.models import WinRatePrediction


import django
django.setup()

def main():
    global gamestats
    gamestats = GameStats.objects.get_or_create(game=game_name)
    print "Preparing anaylsis parameters..."
    win_reasons = []
    try:
        f = open('win_reasons.txt', 'r')
        for line in f:
            win_reasons.append(line)
        f.close()
        gamestats.interesting_win_reasons = win_reasons
        gamestats.save()
    except:
        print "Couldn't read in win_reasons.txt"
        return
    while gamestats.numPlayed < 100:
        for x in Game.objects.all().filter(score=-5).filter(status="Complete"):
            url = x.gamelog_url
    
            file_name = url.split('/')[-1]
            u = urllib2.urlopen(url)
            f = open(file_name, 'wb')
            meta = u.info()
            file_size = int(meta.getheaders("Content-Length")[0])
            print "Downloading: %s Bytes: %s" % (file_name, file_size)

            file_size_dl = 0
            block_sz = 8192
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break

                file_size_dl += len(buffer)
                f.write(buffer)
                status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                status = status + chr(8)*(len(status)+1)
                print status,

            f.close()
            charactors = 0
            with open(file_name, 'r') as in_file:
                for line in in_file:
                    charactors += len(line)
            os.remove(file_name)
            if charactors > gamestats.maxSize:
                gamestats.maxSize = charactors
            gamestats.numPlayed += 1
            gamestats.save()
            x.score = -5
            x.save()
            if gamestats.numplayed >= 100:
                break
        time.sleep(10)
    
    for x in Game.objects.all().filter(score=-5):
        x.score = -1
        x.save()
    print "Starting parameters defined! Let's begin...."
    while True:
        for x in Game.objects.all().filter(score=-1).filter(status="Complete"):
            x.score = 0
            x.save()
            p = Process(target=analyse_game, args=(x,))
            print "Now analysing game", x
            p.start()
        time.sleep(10)

def analyse_game(game):
    url = game.gamelog_url

    file_name = url.split('/')[-1]
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,

    f.close()
    charactors = 0
    with open(file_name, 'r') as in_file:
        for line in in_file:
            charactors += len(line)
    os.remove(file_name)
    if charactors > gamestats.maxSize:
        gamestats.maxSize = charactors
    gamestats.numPlayed += 1
    gamestats.save()
    
    #Begin scoring
    if charactors > (gamestats.maxSize * 0.4) and charactors < (gamestats.maxSize * 0.8):
        game.score += 1
        print "Game", game, "is an interesting length!"
    if not game.discon_happened:
        game.score += 2
        print "No one in game", game, "disconnected!"
    for wumbo in gamestats.interesting_win_reasons:
        if game.win_reason == wumbo:
            game.score += 3
            print "WUMBO!!!!"
            break
    game.save()
    return

if __name__ == "__main__":
    main()
