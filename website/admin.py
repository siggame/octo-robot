#####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Django Imports
from django.contrib import admin

# My Imports
from thunderdome.models import Client, Game, GameData, Referee

class GameDataAdmin(admin.ModelAdmin):
    list_display = ('pk','game','client','won')
    raw_id_fields = ('game',)
    readonly_fields = ('game','client')

admin.site.register(Client)
admin.site.register(Game)
admin.site.register(GameData,GameDataAdmin)
admin.site.register(Referee)
