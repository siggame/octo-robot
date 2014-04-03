import os
import socket
import fcntl
import struct

def get_interface_ip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])


if __name__ == "__main__":
    interfaces = ["eth0", "eth1", "eth2"]
    for ifname in interfaces:
        try:
            print get_interface_ip(ifname)
        except IOError:
            pass
        
