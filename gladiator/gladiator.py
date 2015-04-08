import os
import subprocess
import multiprocessing
import time
import shutil

def start_server(current_server=None):
    if not current_server:
        print "Starting server"
        return subprocess.Popen(['python', 'main.py'], cwd=os.environ['SERVER_PATH'])
    else:
        print "Restarting server"
        current_server.kill()
        return start_server()

def make_ref_folder(ref_id):
    if os.path.exists(str(ref_id)):
        shutil.copyfile('referee.py', "%d/referee.py" % (ref_id))
        shutil.copyfile('prep_for_bake.py', "%d/prep_for_bake.py" % (ref_id))
    else:
        os.mkdir(str(ref_id))
        make_ref_folder(ref_id)

def start_referee(ref_id, games_to_play):
    make_ref_folder(ref_id)
    print "Starting referee", ref_id
    return subprocess.Popen(['python', 'referee.py'],
                            cwd="%d" % ref_id)

def main():
    ref_count = 2
    server_p = start_server()
    referees = [start_referee(i) for i in range(1, ref_count+1)]
    while True:
        for i in list(referees):
            if i.poll() is not None:
                referees.remove(i)
        if not referees:
            server_p = start_server(server_p)
            referees = [start_referee(i) for i in range(1, ref_count+1)]
        else:
            time.sleep(10)
        
if __name__ == "__main__":
    main()
