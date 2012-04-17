#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# FIX base_path

game_name = "megaminerai-9-space"

import urllib
import os
import subprocess
import json

def main():
    api_url = "http://megaminerai.com/api/git/repo?c=%s" % game_name
    f = urllib.urlopen(api_url)
    data = json.loads(f.read())
    f.close()

    for block in data:
        if block['tag'] is not None:
            update_local_repo(block)


def update_local_repo(client):
    '''Get the appropriate code and version from the repository'''
    base_path = os.environ['CLIENT_PREFIX']
    subprocess.call(['git', 'clone', 
                     '%s%s' % (base_path, client['path']), client['login']],
                    stdout=file('%s-gitout.txt' % client['login'], 'w'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'checkout', 'master'], cwd=client['login'],
                    stdout=file('%s-gitout.txt' % client['login'], 'a'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'pull'], cwd=client['login'],
                    stdout=file('%s-gitout.txt' % client['login'], 'a'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'checkout', client['tag']],
                    stdout=file('%s-gitout.txt' % client['login'], 'a'),
                    stderr=subprocess.STDOUT,
                    cwd=client['login'])

main()
