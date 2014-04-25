import socket
import sys
import threading
import re
import time

middle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
referee = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


server_pattern = '\(\\\\"game-winner\\\\"'
client_pattern = "\(request-log "


class ClientPasser(threading.Thread):
    def __init__(self, from_s, to_s):
        self.recieve_from = from_s
        self.send_to = to_s
        self.c_name = "client"
        self.log_requested = False
        self.pattern = '\(request-log '
        threading.Thread.__init__(self)
        self.client_login = False

    def run(self):
        while 1:
            try:
                data = self.recieve_from.recv(10000)
            except socket.timeout:
                data = None
            if data is not None and not self.client_login:
                referee.send_to.sendall('client_login')
                
                self.client_login = True

            if data is not None:
                print "%s: %s" % (self.c_name, data)
                
                if data == '':
                    print "client has finished"
                    break

                self.send_to.sendall(data)


class ServerPasser(threading.Thread):
    def __init__(self, from_s, to_s, client_passer):
        self.recieve_from = from_s
        self.send_to = to_s
        self.c_name = "server"
        self.client_passer = client_passer
        threading.Thread.__init__(self)

    def run(self):
        while self.client_passer.is_alive():
            try:
                data = self.recieve_from.recv(100000)
            except socket.timeout:
                data = None

            if data is not None:
                print "%s: %s" % (self.c_name, data)
                self.send_to.sendall(data)


class RecvSend(threading.Thread):
    def __init__(self, from_s, to_s, name, client=None):
        self.recieve_from = from_s
        self.send_to = to_s
        self.c_name = name
        self.done = False
        self.client_che = client
        threading.Thread.__init__(self)
        
    def run(self):
        while not self.done:
            try:
                data = self.recieve_from.recv(100000)
            except socket.timeout:
                #print "timeout except caught"
                data = None
            if data is not None:
                print "%s: %s" % (self.c_name, repr(data))
                self.send_to.sendall(data)
                m = re.search(server_pattern, data) is not None
                t = re.search(client_pattern, data) is not None
                if data == '' or t or m:
                    print "%s has finished" % self.c_name
                    break

    def end_run(self):
        self.done = True
    
s_host = sys.argv[1]
s_port = int(sys.argv[2])

m_host = sys.argv[3]
m_port = int(sys.argv[4])

r_host = 'localhost'
r_port = int(sys.argv[5])

middle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
middle.bind((m_host, m_port))

time.sleep(10)

# this is where a ping should be sent to the client's machine

referee.connect(('localhost', r_port))
referee.settimeout(0.5)



# send a message to the referee to do a job update so the archiver can process the job
# which then gets updated on the db then people can refesh page and see the stuff

middle.listen(1)
conn, addr = middle.accept()

#connect to server
server.connect((s_host, s_port))

conn.settimeout(0.5)
server.settimeout(0.5)

client_s = ClientPasser(conn, server)
server_c = ServerPasser(server, conn, client_s)

client_s.start()
server_c.start()

while client_s.is_alive() or server_c.is_alive():
    time.sleep(3)

middle.close()
conn.close()
server.close()
