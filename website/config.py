#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
### Configuration file for the arena
### also integrates bootstrap.py written by Stephen Jackson <scj7t4@mst.edu>
#####

from aws_secrets import access_cred, secret_cred

game_name = 'megaminerai-10-galapagos'
beanstalk_host = 'arena.megaminerai.com'
arena_ami = 'ami-94bd07fd'
tournament_ami = 'ami-acc743c5'
req_queue_len = 5
