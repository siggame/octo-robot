#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

import urllib
import os
import subprocess
import json

import requests

game_name = os.environ["GAME_NAME"]

WEB_USER = 'arena'
WEB_PASS = ""

def main():
    api_url = "http://megaminerai.com/api/repo/tags/%s" % game_name
    r = requests.get(api_url, auth=(WEB_USER, WEB_PASS), verify=False)
    try:
        data = json.loads(r.text)
    except ValueError:
        data = []
        print r.text
    
    #f = urllib.urlopen(api_url)
    #data = json.loads(f.read())
    #f.close()
    
    for block in data:
        if block['team']['slug'] is not None:
            print block['team']['slug'], block['tag']['commit']
            update_local_repo(block)

def update_local_repo(client):
    '''Get the appropriate code and version from the repository'''
    base_path = os.environ['CLIENT_PREFIX']
    subprocess.call(['rm', '-rf', '%s' % client['team']['slug']],
                    stdout=file('/dev/null'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'clone',
                     '%s%s' % (base_path, client['repository']['path']), client['team']['slug']],
                    stdout=file('%s-gitout.txt' % client['team']['slug'], 'w'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'checkout', 'master'], cwd=client['team']['slug'],
                    stdout=file('%s-gitout.txt' % client['team']['slug'], 'a'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'pull'], cwd=client['team']['slug'],
                    stdout=file('%s-gitout.txt' % client['team']['slug'], 'a'),
                    stderr=subprocess.STDOUT)
    subprocess.call(['git', 'checkout', client['tag']['commit']],
                    stdout=file('%s-gitout.txt' % client['team']['slug'], 'a'),
                    stderr=subprocess.STDOUT,
                    cwd=client['team']['slug'])

main()
