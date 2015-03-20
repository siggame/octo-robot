import urllib
import os
import sys

def download_glog(url, download_destination='.'):
    absolute_path = os.path.abspath(os.path.join('.', download_destination))
    print os.path.exists(absolute_path)
    if not os.path.exists(absolute_path):
        os.mkdir(absolute_path)
    urlreader = urllib.urlopen(url)
    data = urlreader.read()
    filepath = os.path.join(absolute_path, glog_name(url))
    filewriter = open(filepath, 'w')
    filewriter.write(data)
    filewriter.close()

def glog_name(url):
    t = url.split('/')
    return t[len(t)-1]


def main():
    download_glog("http://siggame-arena-test-bucket.s3.amazonaws.com/logs/megaminerai-15-pharaoh/859-02771.glog", 'var/static/gladiator')


if __name__ == "__main__":
    main()
