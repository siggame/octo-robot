#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Some magic to get a standalone python program hooked in to django
import sys, os
sys.path = ['/home/gladiator', '/home/gladiator/djangolol'] + sys.path

from django.core.management import setup_environ
import settings

setup_environ(settings)

# Non-Django 3rd Party Imports
import subprocess

from thunderdome.models import Client, Game

def main():
    for c in Client.objects.all():
        c.rating = 2300
        c.score = 0
        c.save()
    
    for g in Game.objects.all():
        g.delete()
        
main()
