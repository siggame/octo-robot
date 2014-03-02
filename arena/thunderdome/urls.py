#####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

from django.conf.urls.defaults import patterns, url, include
from tastypie.api import Api
#from thunderdome.api import 

urlpatterns = patterns(
    'thunderdome.views',
    url(r'^$', 'scoreboard'),
    url(r'^health$', 'health'),
    url(r'^view/(?P<game_id>\d+)$', 'view_game'),
)
