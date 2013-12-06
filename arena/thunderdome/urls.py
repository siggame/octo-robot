from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns(
    'thunderdome.views',
    url(r'^$', 'index'),
    url(r'^view/(?P<game_id>\d+)$', 'view_game'),
)
