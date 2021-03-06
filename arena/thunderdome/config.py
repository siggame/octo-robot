#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
### Configuration file for the arena
### also integrates bootstrap.py written by Stephen Jackson <scj7t@mst.edu>
#####


from arena.settings.aws_secrets import access_cred, secret_cred, s3_prefix
from arena.settings.secret_settings import WEBSITE_USER_NAME, WEBSITE_ARENA_PASSWORD
from thunderdome.models import ArenaConfig

a = ArenaConfig.objects.get(active=True)

game_name = a.game_name
beanstalk_host = a.beanstalk_host
client_prefix = a.client_prefix
req_queue_len = a.req_queue_length
api_url_template = a.api_url_template
client_port = a.client_port
web_client_port = a.web_client_port
api_port = a.api_port
persistent = a.persistent
mode = a.mode

arena_ami = 'ami-ab61ccd1' # current gladiator image id
tournament_ami = 'ami-ab61ccd1' #'ami-a221a9ca' # old touranment
