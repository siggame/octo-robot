
import json
import os
from thunderdome.models import ArenaConfig

def save_settings(setting_loc=os.path.join(os.path.dirname(__file__), 'configs.json')):
    arena_settings = list(ArenaConfig.objects.all())
    k = []
    for i in arena_settings:
        dict_t = {}
        dict_t.update({'game_name' : i.game_name})
        dict_t.update({'beanstalk_host' : i.beanstalk_host})
        dict_t.update({'client_prefix' : i.client_prefix})
        dict_t.update({'req_queue_length' : i.req_queue_length})
        dict_t.update({'config_name' : i.config_name})
        k.append(dict_t)
    filer = open(setting_loc, 'w')
    filer.write(json.dumps(k, indent=1))
    filer.close()

def load_settings(setting_loc=os.path.join(os.path.dirname(__file__), 'configs.json')):
    filer = open(setting_loc)
    k = json.load(filer)
    for i in k:
        temp_config = ArenaConfig.objects.get_or_create(config_name=i['config_name'])[0]
        temp_config.beanstalk_host = i['beanstalk_host']
        temp_config.client_prefix = i['client_prefix']
        temp_config.req_queue_length = int(i['req_queue_length'])
        temp_config.game_name = i['game_name']
        temp_config.save()


if __name__ == "__main__":
    save_settings()
