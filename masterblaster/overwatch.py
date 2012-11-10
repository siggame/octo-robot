#!/usr/bin/env python

# Standard Imports
from time import sleep
import logging
import json
import re

# Non-Django 3rd Party Imports
import psutil
import hoover

siggame_arena_json = "10d4882c-8892-4496-a4ff-4002a21f297b"

handler = hoover.LogglyHttpHandler(token=siggame_arena_json)
log = logging.getLogger('Arena')
log.addHandler(handler)
log.setLevel(logging.DEBUG)


def report():
    payload = {'memory_report': 'yep'}
    for p in psutil.process_iter():
        full_cmd = ' '.join(p.cmdline)
        if re.search('archiver', full_cmd):
            payload['archiver'] = p.get_memory_percent()
        elif re.search('scheduler', full_cmd):
            payload['scheduler'] = p.get_memory_percent()
    log.info(json.dumps(payload))
    print json.dumps(payload)


def main():
    while True:
        report()
        sleep(30)


main()
