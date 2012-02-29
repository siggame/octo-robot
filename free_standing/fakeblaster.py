#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

import subprocess
import time

def main():
    for i in xrange(200):
        start_fake_referee()
    while True:
        time.sleep(1)

        
def start_fake_referee():
    return subprocess.Popen(['./fakeref.py'])


main()
