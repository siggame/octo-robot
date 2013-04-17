#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
### Configuration file for the arena
### also integrates bootstrap.py written by Stephen Jackson <scj7t4@mst.edu>
#####

from aws_secrets import access_cred, secret_cred

game_name = 'megaminerai-11-reef'
beanstalk_host = 'arena.megaminerai.com'
arena_ami = 'ami-8c492fe5'
tournament_ami = 'ami-84adcbed'
req_queue_len = 5
