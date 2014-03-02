from __future__ import absolute_import

from celeryglad.celery import app

@app.task
def playgame(guy0, guy1, origin):
    print guy0, guy1, origin
    
    return 0

