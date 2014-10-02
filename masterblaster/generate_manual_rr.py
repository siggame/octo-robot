
from thunderdome.models import Client
from itertools import combinations
import json

def roundRobin(groupTP, groupUP, numGames):
    result = list()
    for guy in groupTP:
        for otherguy in groupUP:
            for counter in range(numGames):
                if counter % 2:
                    result.append((guy, otherguy))
                else:
                    result.append((otherguy, guy))
    return result

def main():
    clients = list(Client.objects.filter(eligible=True).filter(embargoed=False))

    for i in list(clients):
        stats = json.loads(i.stats)
        if stats['language'] == 'Human':
            clients.remove(i)
    
    pondering_ais = []
    pondering_ais.append(Client.objects.get(name='cole-xemi'))
    pondering_ais.append(Client.objects.get(name='derek-allen'))
    pondering_ais.append(Client.objects.get(name='jrtfkb'))
    pondering_ais.append(Client.objects.get(name='nftn83'))
    pondering_ais.append(Client.objects.get(name='waw'))

    clients.extend(pondering_ais)
    results = roundRobin(pondering_ais, clients, 2)
    s = open('manual_gamesAuto.txt', 'w')
    for i in results:
        s.write("%s %s\n" % (i[0].name, i[1].name))
        s.flush()
    s.close()


if __name__ == "__main__":
    main()
    
                         
