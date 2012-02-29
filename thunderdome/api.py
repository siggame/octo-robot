from tastypie.resources import ModelResource
from tastypie import fields
from thunderdome.models import Client, Game

class GameResource(ModelResource):
    winner = fields.ForeignKey('thunderdome.api.ClientNameResource', 'winner', null=True, full=True)
    loser = fields.ForeignKey('thunderdome.api.ClientNameResource', 'loser', null=True, full=True)
    class Meta:
        queryset = Game.objects.all()
        fields = ['gamelog_url', 'status', 'winner', 'loser']
        allowed_methods = ['get']


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
        filtering = { 'name': ['exact'] }
