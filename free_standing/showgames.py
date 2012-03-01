#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####


import subprocess, re, os

def main():
    # prime the loop
    next_gamelog_url = get_next_gamelog_url()
    next_gamelog_filename = grab_filename(next_gamelog_url)
    gamelog_filename = next_gamelog_filename
    subprocess.call(['wget', '-N', next_gamelog_url])
    
    while True:
        # concept here is that we want to grab the next gamelog
        # while the current gamelog is playing
        show = subprocess.Popen(['visualizer.exe', gamelog_filename])
        mark_game_visualized(next_gamelog_url)
        next_gamelog_url = get_next_gamelog_url()
        next_gamelog_filename = grab_filename(next_gamelog_url)
        grab = subprocess.Popen(['wget', '-N', next_gamelog_url])    
        [x.wait() for x in (show,grab)]
        os.remove(gamelog_filename)
        gamelog_filename = next_gamelog_filename


def grab_filename(url):
    m = re.search('\d+-[\w]+\.glog$', url)
    return m.group(0) if m else None


def grab_game_number(url):
    m = re.search('(\d+)-[\w]+\.glog$', url)
    return m.group(1) if m else None


def get_next_gamelog_url():
    subprocess.call(['wget', '-N',
                     'http://mnuck.com/mies/thunderdome/get_next_game_url_to_visualize'])
    f = open('get_next_game_url_to_visualize', 'r')
    line = f.readline()
    f.close()
    os.remove('get_next_game_url_to_visualize')
    return line
    

def mark_game_visualized(game_url):
    number = grab_game_number(game_url)
    subprocess.call(['wget', '-N',
                     'http://mnuck.com/mies/thunderdome/game_visualized/%s' % number])
    os.remove(number)

main()
