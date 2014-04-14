import os
import socket
import fcntl
import struct
import boto
from boto import ec2
from pprint import pprint

def get_interface_ip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])

def get_gladiator_public_ip():
    
    ec2conn = boto.connect_ec2(os['ACCESS_CRED'], os['SECRET_CRED'])
    reservations = ec2conn.get_all_instances()
    instances = [i for r in reservations for i in r.instances]

    possible_ips = [["eth0", None], ["eth1", None]]
    for i in possible_ips:
        try:
            i[1] = get_interface_ip(i[0])
        except:
            pass

    public_ip_address = None
    print possible_ips    
    for i in instances:
        for j in possible_ips:
            print j, i.private_ip_address
            if str(i.private_ip_address) == str(j[1]) and j[1] is not None:
                print "setting public ip address"
                public_ip_address = i.ip_address            
        
    if public_ip_address is not None:
        return public_ip_address
    else:
        return possible_ips[1][1]

t = get_gladiator_public_ip

if __name__ == "__main__":
    print t()
    #interfaces = ["eth0", "eth1", "eth2"]
    #for ifname in interfaces:
    #    try:
    #        print get_interface_ip(ifname)
    #    except IOError:
    #        pass
        
