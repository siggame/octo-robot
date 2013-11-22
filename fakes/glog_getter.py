import shutil
import os
import bootstrap
import urllib2
import tarfile

from thunderdome.models import Match, Game

pat = "http://siggame-glog-megaminerai-12-mars.s3.amazonaws.com/"

tourny_numb = 201309
base_dir = "tournament_games%d/" % tourny_numb

file_dirs = []

def glogdump(tournament_numb):
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    match = Match.objects.filter(tournament=tournament_numb)
    matches = [i for i in match if i.p0.name != 'bye' and i.p1.name != 'bye']
    
    for match in matches:
        p0_directory = match.p0.name
        p1_directory = match.p1.name
        if p0_directory not in file_dirs:
            file_dirs.append(p0_directory)
        if p1_directory not in file_dirs:
            file_dirs.append(p1_directory)
        dir1 = base_dir + p0_directory + "/" + p1_directory
        dir2 = base_dir + p1_directory + "/" + p0_directory
        if not os.path.exists(dir1):
            os.makedirs(dir1)
        if not os.path.exists(dir2):
            os.makedirs(dir2)
        for game in match.games.all():
            try:
                f = urllib2.urlopen(game.gamelog_url)
                data = f.read()
                # data = Decompress.decompress(f.read())
            except:
                pass
            glog_num = game.gamelog_url.replace(pat, '')
            writer = open(dir1 + "/"+ glog_num, 'w')
            writer.write(data)
            writer.close()
            writer = open(dir2 + "/" + glog_num, 'w')
            writer.write(data)
            writer.close()

def tar_folders():
    for c1 in list(file_dirs):
        tarwriter = tarfile.open(base_dir + "/" + c1 + ".tar.gz", "w:gz")
        for c2 in list(file_dirs):
            try:
                tarwriter.add(base_dir + "/" + c1 + "/" + c2)
            except:
                pass
        tarwriter.close()

def remove_folders():
    for c1 in list(file_dirs):
        shutil.rmtree(base_dir + "/" + c1)


if __name__ == "__main__":
    print "getting glogs"
    glogdump(tourny_numb)
    #print "taring folders"
    #tar_folders()
    #print "removing untareds"
    #remove_folders()
