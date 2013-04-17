#####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

from django.conf.urls.defaults import patterns, url, include
from tastypie.api import Api
from thunderdome.api import ClientResource, ClientNameResource, GameResource, GameDataResource, MatchResource

v1_api = Api(api_name='v1')
v1_api.register(ClientResource())
v1_api.register(ClientNameResource())
v1_api.register(GameResource())
v1_api.register(GameDataResource())
v1_api.register(MatchResource())

urlpatterns = patterns('thunderdome.views',
    url(r'^end_rr$', 'end_rr'),
    url(r'^bet_list$', 'bet_list'),
    url(r'^main$', 'scoreboard'),
    url(r'^$', 'scoreboard'),
    url(r'^inject$', 'inject'),
    url(r'^view/(?P<game_id>\d+)$', 'view_game'),

    #url(r'^view/main$', 'scoreboard'), #-brad, not needed at the moment, but has possiblity

    url(r'^get_next_game_url_to_visualize$', 'get_next_game_url_to_visualize'),
    url(r'^game_visualized/(?P<game_id>\d+)$', 'game_visualized'),
    url(r'^get_next_game_url_to_visualize_and_mark', 'get_and_mark'),
   
    url(r'^chart/scoreboard$', 'scoreboard_chart'),                 
    url(r'^chart/throughput$', 'throughput_chart'),
    url(r'^health$', 'health'),
    url(r'^view_client/(?P<client_id>\d+)$', 'view_client'),
    url(r'^view_match/(?P<match_id>\d+)$', 'view_match'),
    url(r'^matchup/(?P<client1_id>\d+)vs(?P<client2_id>\d+)$', 'matchup'),
    url(r'^visualize/(?P<game_id>\d+)$', 'visualize'),
    url(r'^represent/(?P<match_id>\d+)$', 'representative_game'),
    url(r'^visualize_match/(?P<match_id>\d+)$', 'visualize_match'),
    url(r'^api/', include(v1_api.urls)),
    #url for rating games, game id followed by rating from 0-9
    url(r'^rate/(?P<game_id>\d+)/(?P<rating>\d+)$', 'rate_game')
)
