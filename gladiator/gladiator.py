import os
import subprocess
import multiprocessing
import time
import shutil

from referee import start_ref

def start_server(current_server=None):
    if not current_server:
        return subprocess.Popen(['python', 'main.py'], cwd=os.environ['SERVER_PATH'])
    else:
        current_server.kill()
        return start_server()

def make_ref_folder(ref_id):
    if os.path.exists(ref_id):
        shutil.copyfile('referee.py', "%d/referee.py" % (ref_id))
        shutil.copyfile('prep_for_bake.py', "%d/prep_for_bake.py" % (ref_id))
    else:
        os.mkdir(ref_id)
        make_ref_folder(ref_id)

def start_referee(ref_id, games_to_play):
    make_ref_folder(ref_id)
    return subprocess.Popen(['python', 'referee.py'], cwd="ref_id")

def main():
    ref_count = 1
    total_games_per_server = 1000
    server_p = start_server()
    referees = [start_referee(i) for i in range(1, ref_count+1)]
    while True:
        if cur_time < wait_time:
            time.sleep(wait_time)
        else:
            server_p = start_server(server_p)
        
if __name__ == "__main__":
    make_ref_folder(1)
