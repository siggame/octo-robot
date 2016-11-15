
from thunderdome.config import game_name
import beanstalkc

def empty_tube():
    tube = 'game-requests-' + game_name
    c = beanstalkc.Connection()
    c.watch(tube)
    while c.stats_tube(tube)['current-jobs-ready'] > 0:
        j = c.reserve()
        j.delete()
    tube = 'game-results-' + game_name
    c = beanstalkc.Connection()
    c.watch(tube)
    while c.stats_tube(tube)['current-jobs-ready'] > 0:
        j = c.reserve()
        j.delete()


if __name__ == "__main__":
    empty_tube()
