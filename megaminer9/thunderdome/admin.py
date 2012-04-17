#####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

from thunderdome.models import Client, Game, GameData, Referee
from django.contrib import admin

admin.site.register(Client)
admin.site.register(Game)
admin.site.register(GameData)
admin.site.register(Referee)
