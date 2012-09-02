#####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie import fields
from thunderdome.models import Client, Game, GameData, Match

class MatchResource(ModelResource):
    p0     = fields.ForeignKey('thunderdome.api.ClientNameResource', 'p0',     null=True, full=True)
    p1     = fields.ForeignKey('thunderdome.api.ClientNameResource', 'p1',     null=True, full=True)
    winner = fields.ForeignKey('thunderdome.api.ClientNameResource', 'winner', null=True, full=True)
    loser  = fields.ForeignKey('thunderdome.api.ClientNameResource', 'loser',  null=True, full=True)
    father = fields.ForeignKey('thunderdome.api.MatchResource',      'father', null=True, full=False)
    mother = fields.ForeignKey('thunderdome.api.MatchResource',      'mother', null=True, full=False)
    class Meta:
        queryset = Match.objects.all()


class GameDataResource(ModelResource):
    name = fields.ForeignKey('thunderdome.api.ClientNameResource', 'client', null=True, full=True)
    game = fields.ForeignKey('thunderdome.api.GameResource',       'game',   null=True, full=True)
    class Meta:
        queryset = GameData.objects.all()
        ordering = ['game']
        resource_name = 'game_data'
        fields = ['name', 'output_url', 'version']
        filtering = {'name' : ALL_WITH_RELATIONS,
                     'game' : ALL_WITH_RELATIONS}


class GameResource(ModelResource):
    winner = fields.ForeignKey('thunderdome.api.ClientNameResource', 'winner', null=True, full=True)
    loser  = fields.ForeignKey('thunderdome.api.ClientNameResource', 'loser',  null=True, full=True)
    game_data = fields.ToManyField(GameDataResource, 'gamedata_set', full=False, null=True)
    class Meta:
        queryset = Game.objects.all()
        fields = ['gamelog_url', 'status', 'winner', 'loser', 'completed']
        allowed_methods = ['get']
        ordering = ['completed']
        filtering = {'winner' : ALL_WITH_RELATIONS,
                     'loser'  : ALL_WITH_RELATIONS}
        

class ClientNameResource(ModelResource):
    class Meta:
        queryset = Client.objects.all()
        fields = ['name']
        allowed_methods = ['get']
        filtering = {'name' : ['exact']}
        

class ClientResource(ModelResource):
    class Meta:
        queryset = Client.objects.all()
        excludes = ['seed']
        allowed_methods = ['get']
        filtering = {'name'         : ['exact'],
                     'games_played' : ['exact']}
