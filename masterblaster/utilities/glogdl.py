import urllib
import os
import sys

from thunderdome.models import Game

def get_glog_data(url):
    urlreader = urllib.urlopen(url)
    data = urlreader.read()
    return data

def write_file(data, file_name, path='.'):
    absolute_path = os.path.abspath(os.path.join('.', path))
    if not os.path.exists(absolute_path):
        os.mkdir(absolute_path)
    filewriter = open(os.path.join(absolute_path, file_name), 'w')
    filewriter.write(data)
    filewriter.close()

def download_glog(url, download_destinations=None):
    if download_destinations is None:
        download_destinations = ['.']
    else:
        if type(download_destinations) is type(""):
            download_destinations = [download_destinations]
    data = get_glog_data(url)
    filename = glog_name(url)
    for i in download_destinations:
        write_file(data, filename, i)

def glog_name(url):
    t = url.split('/')
    return t[len(t)-1]

def download_all_gamelogs(download_folder='var/static/gladiator'):
    for i in list(Game.objects.all()):
        if i.gamelog_url:
            clients = list(i.clients.all())
            client_folder1 = os.path.join(download_folder, clients[0].name)
            client_folder2 = os.path.join(download_folder, clients[1].name)
            download_glog(i.gamelog_url, [client_folder1, client_folder2])

def main():
    download_glog("http://siggame-arena-test-bucket.s3.amazonaws.com/logs/megaminerai-15-pharaoh/859-02771.glog", ['var/static/gladiator/client1', 'var/static/gladiator/client2'])


if __name__ == "__main__":
    main()
