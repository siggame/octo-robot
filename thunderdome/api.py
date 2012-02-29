from tastypie.resources import ModelResource
from tastypie import fields
from thunderdome.models import Client, Game, GameData

class GameDataResource(ModelResource):
    name = fields.ForeignKey('thunderdome.api.ClientNameResource', 'client', null=True, full=True)
#    game = fields.ForeignKey('thunderdome.api.GameResource', 'game', null=True, full=True)
    class Meta:
        queryset = GameData.objects.all()
        resource_name = 'game_data'
        fields = ['name', 'output_url']


class GameResource(ModelResource):
    winner = fields.ForeignKey('thunderdome.api.ClientNameResource', 'winner', null=True, full=True)
    loser = fields.ForeignKey('thunderdome.api.ClientNameResource', 'loser', null=True, full=True)
    game_data = fields.ToManyField(GameDataResource, 'gamedata_set', full=True, null=True)
    class Meta:
        queryset = Game.objects.all()
        fields = ['gamelog_url', 'status', 'winner', 'loser', 'completed']
        allowed_methods = ['get']
        ordering = ['completed']
        


class ClientNameResource(ModelResource):
    class Meta:
        queryset = Client.objects.all()
        fields = ['name']
        allowed_methods = ['get']
    
        
class ClientResource(ModelResource):
    games_played = fields.ToManyField(GameResource, 'games_played', full=True, null=True)
    class Meta:
        queryset = Client.objects.all()
        excludes = ['seed']
        allowed_methods = ['get']
        filtering = { 'name'         : ['exact'],
                      'games_played' : ['exact']}
        
