import django
django.setup()

from thunderdome.models import Client, Game

p0 = raw_input('Player 1: ')
p1 = raw_input('Player 2: ')
games = Game.objects.all()
found = False
for g in games:
    if g.status == 'Complete':
        current_game = Game.objects.get(pk=g.pk)
        game_clients = list(current_game.clients.all())
        if game_clients[0].name == p0 and game_clients[1].name == p1:
            found = True
            if g.tied:
                print '\nDraw!'
            else:
                print '\nWinner:', g.winner.name
                print 'Loser:', g.loser.name
if not found:
    print "\nGame not found"
