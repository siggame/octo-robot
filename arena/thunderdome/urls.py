
#####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

from django.conf.urls import patterns, url, include
from tastypie.api import Api
from thunderdome.api import ClientResource, ClientNameResource, GameResource, GameDataResource, MatchResource

v1_api = Api(api_name='v1')
v1_api.register(ClientResource())
v1_api.register(ClientNameResource())
v1_api.register(GameResource())
v1_api.register(GameDataResource())
v1_api.register(MatchResource())

urlpatterns = patterns(
    'thunderdome.views',
    url(r'^$', 'index'),
    url(r'^health$', 'health'),
    url(r'^view/(?P<game_id>\d+)$', 'view_game'),
    url(r'^view_match/(?P<match_id>\d+)$', 'view_match', name='matchy'),
    url(r'^rate_game/(?P<game_id>\d+)/(?P<rating>\d+)', 'rate_game'),
    url(r'^represent/(?P<match_id>\d+)$', 'representative_game'),
    url(r'^inject$', 'inject'),
    url(r'^get_next_game$', 'get_next_game_url_to_visualize'),
    url(r'^scoreboard$', 'scoreboard'),
    url(r'^logout$', 'logout_view'),
    url(r'^settings$', 'settings'),

    url(r'^clients$', 'display_clients'),
    url(r'^swissTurn$', 'human_swiss'),
    url(r'^api/', include(v1_api.urls)),
    url(r'^api/get_scores$', 'get_scores'),
)
