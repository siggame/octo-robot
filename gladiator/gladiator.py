import os
import subprocess
import time

def start_server(current_server=None):
    if not current_server:
        return subprocess.Popen(['python', 'main.py'], cwd=os.environ['SERVER_PATH'])
    else:
        current_server.kill()
        return start_server()

def start_referee(ref_id):
    if os.path.exists(ref_id):
        return subprocess.Popen(['python', 'referee.py'], cwd=ref_id)
    else:
        os.mkdir(ref_id)
        return start_referee(ref_id)

def main():
    ref_count = 1
    server_p = start_server()
    referees = [start_referee(i) for i in range(1, ref_count+1)]
    while True:
        if cur_time < wait_time:
            time.sleep(wait_time)
        else:
            server_p = start_server(server_p)
        
if __name__ == "__main__":
    main()
