#####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

from django.conf.urls.defaults import patterns, url, include
from tastypie.api import Api
from thunderdome.api import ClientResource, ClientNameResource, GameResource

v1_api = Api(api_name='v1')
v1_api.register(ClientResource())
v1_api.register(ClientNameResource())
v1_api.register(GameResource())

urlpatterns = patterns('thunderdome.views',
    url(r'^bet_list$', 'bet_list'),
    url(r'^$','scoreboard'),
    url(r'^inject$', 'inject'),
    url(r'^view/(?P<game_id>\d+)$', 'view_game'),
    
    url(r'^get_next_game_url_to_visualize$', 'get_next_game_url_to_visualize'),
    url(r'^game_visualized/(?P<game_id>\d+)$', 'game_visualized'),
    url(r'^get_next_game_url_to_visualize_and_mark', 'get_and_mark'),
                    
    url(r'^chart$', 'chart'),
    url(r'^health$', 'health'),
    url(r'^view_client/(?P<client_id>\d+)$', 'view_client'),
    url(r'^view_match/(?P<match_id>\d+)$', 'view_match'),
    url(r'^matchup/(?P<client1_id>\d+)vs(?P<client2_id>\d+)$', 'matchup'),
    url(r'^api/', include(v1_api.urls)),
    url(r'^visualize/(?P<game_id>\d+)$', 'visualize'),
    url(r'^represent/(?P<match_id>\d+)$', 'representative_game'),
    url(r'^visualize_match/(?P<match_id>\d+)$', 'visualize_match'),
)
