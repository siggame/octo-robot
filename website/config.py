#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
### Configuration file for the arena
### also integrates bootstrap.py written by Stephen Jackson <scj7t4@mst.edu>
#####

from aws_secrets import access_cred, secret_cred

game_name = 'megaminerai-9-space'
beanstalk_host = 'arena.mnuck.com'
arena_ami = 'ami-1e32ea77'
tournament_ami = 'ami-????????'
req_queue_len = 5
