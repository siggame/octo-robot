
import json
import os
from thunderdome.models import ArenaConfig

def save_settings(setting_loc=os.path.join(os.path.dirname(__file__), 'configs.json')):
    arena_settings = list(ArenaConfig.objects.all())
    k = []
    for i in arena_settings:
        k.append(i.parameters)
    filer = open(setting_loc, 'w')
    filer.write(json.dumps(k, indent=1))
    filer.close()

def load_settings(setting_loc=os.path.join(os.path.dirname(__file__), 'configs.json')):
    filer = open(setting_loc)
    k = json.load(filer)
    for i in k:
        temp_config = ArenaConfig.objects.get_or_create(config_name=i['config_name'])[0]
        for key in i.keys():
            temp_config.__dict__[key] = i[key]
        temp_config.save()

if __name__ == "__main__":
    save_settings()
