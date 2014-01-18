from __future__ import absolute_import

from celery import Celery

app = Celery('celeryglad',
             broker='amqp://guest@192.168.1.77',
             backend='amqp://guest@192.168.1.77',
             include=['celeryglad.tasks'])


if __name__ == '__main__':
    app.start()
