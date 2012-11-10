#####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Django Imports
from django.contrib import admin

# My Imports
from thunderdome.models import Client, Game, GameData, Referee


admin.site.register(Client)
admin.site.register(Game)
admin.site.register(GameData)
admin.site.register(Referee)
