#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
### Configuration file for the arena
### also integrates bootstrap.py written by Stephen Jackson <scj7t@mst.edu>
#####


from arena.settings.aws_secrets import access_cred, secret_cred, s3_prefix
from arena.settings.secret_settings import WEBSITE_USER_NAME, WEBSITE_ARENA_PASSWORD
        
game_name = ''
beanstalk_host = ''
client_prefix = ''
arena_ami = ''
tournament_ami = ''
req_queue_len = 5
api_url_template = "http://megaminerai.com/api/repo/tags/%s/"
arena_head = ''
