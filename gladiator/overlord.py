#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

import os
import re
from subprocess import Popen, PIPE

server = Popen(['python', 'main.py', '-arena'], stdout=PIPE, stderr=PIPE, cwd="server")
refereeOne = Popen(['python', 'refer.py', os.environ['SERVER_PATH']], stdout=PIPE,
                   stderr=PIPE, stdin=PIPE, cwd='1')

pattern = re.compile('Game [0-9]+ over')

while True:
    if server.poll():
        output = server.stdout.readline()

        if output != '':
            result = pattern.match(output)
            print(result)