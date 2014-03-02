#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
### Configuration file for the arena
### also integrates bootstrap.py written by Stephen Jackson <scj7t@mst.edu>
#####


from arena.settings.aws_secrets import access_cred, secret_cred, s3_prefix
        
game_name = 'megaminerai-12-mars'
beanstalk_host = 'arena.megaminerai.com'
client_prefix = 'ssh://webserver@megaminerai.com'
arena_ami = ''
tournament_ami = ''
req_queue_len = 5
api_url_template = "http://megaminerai.com/api/repo/tags/%s/"
