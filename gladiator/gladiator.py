import os
import subprocess
import multiprocessing
import time
import shutil
import sys

def start_server(current_server=None):
    if not current_server:
        print "Starting server"
        return subprocess.Popen(['npm', 'run', 'js', '--',  '--arena', '--tcp-port', os.environ['CLIENT_PORT'], '--http-port', os.environ['API_PORT'], '--ws-port', os.environ['WEB_CLIENT_PORT']],
                                 stdout=file('server-stdout.txt', 'w'), stderr=file('server-stderr.txt', 'w'), cwd=os.environ['SERVER_PATH'])
    else:
        print "Restarting server"
        current_server.kill()
        return start_server()

def make_ref_folder(ref_id):
    if os.path.exists(str(ref_id)):
        shutil.copyfile('referee.py', "%d/referee.py" % (ref_id))
    else:
        os.mkdir(str(ref_id))
        make_ref_folder(ref_id)

def start_referee(ref_id):
    make_ref_folder(ref_id)
    print "Starting referee", ref_id
    return subprocess.Popen(['python', '-u', 'referee.py'],
                            stdout=file('ref-%d-stdout.txt' % ref_id, 'w'),
                            stderr=file('ref-%d-stderr.txt' % ref_id, 'w'),
                            cwd="%d" % ref_id)

def main():
    if len(sys.argv) > 1:
       ref_count = int(sys.argv[1])
    else:
       ref_count = 1
    time.sleep(10)
    try:
        server_p = start_server()
    except:
        print sys.exc_info()[0]
    referees = []
    running_count = 0
    try:
        for i in range(1, ref_count+1):
            referees.append(start_referee(i))
            running_count += 1
    except:
        print sys.exc_info()[0]
    while True: 
        if server_p.poll() is not None:
            try:
                server_p = start_server()
            except:
                print sys.exc_info()[0]
        for i in list(referees):
            if i.poll() is not None:
                referees.remove(i)
        if len(referees) != ref_count:
            num_startrefs = ref_count - len(referees)
            count = running_count
            try:
                for i in range(count+1, num_startrefs+count+1):
                    referees.append(start_referee(i))
                    running_count += 1
            except:
                print sys.exc_info()[0]
        else:
            time.sleep(10)
        
if __name__ == "__main__":
    main()
