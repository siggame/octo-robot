#####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Tasty Pie Imports
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie import fields

# My Imports
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
    game = fields.ForeignKey('thunderdome.api.GameResource',       'game',   null=True, full=False)
    class Meta:
        queryset = GameData.objects.all().order_by('-game')
        ordering = ['-game']
        resource_name = 'game_data'
        fields = ['name', 'output_url', 'version','id','won']
        filtering = {'name' : ALL_WITH_RELATIONS,
                     'game' : ALL_WITH_RELATIONS}


class GameResource(ModelResource):
    winner = fields.ForeignKey('thunderdome.api.ClientNameResource', 'winner', null=True, full=True)
    loser  = fields.ForeignKey('thunderdome.api.ClientNameResource', 'loser',  null=True, full=True)
    clients = fields.ToManyField('thunderdome.api.ClientNameResource', 'clients', full=True)
    winreason = fields.CharField('thunderdome.api.GameResource', 'win_reason')
    losereason = fields.CharField('thunderdome.api.GameResource', 'lose_reason')
    game_data = fields.ToManyField(GameDataResource, 'gamedata_set', full=True, null=True)
    class Meta:
        queryset = Game.objects.all().order_by('-pk')
        #ordering = ['id']
        fields = ['gamelog_url', 'status', 'winner', 'loser', 'completed','id','win_reason','lose_reason']
        allowed_methods = ['get']
        ordering = ['completed']
        filtering = {'winner' : ALL_WITH_RELATIONS,
                     'loser'  : ALL_WITH_RELATIONS,
                     'id'     : ['exact']}
        

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
