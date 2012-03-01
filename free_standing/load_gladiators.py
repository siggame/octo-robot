#!/usr/bin/env python

from aws_creds import access_cred, secret_cred
import boto

f = open('user-data', 'r')
user_data = f.read()
f.close()

count = 1
print "spinning up %i gladiators..." % count
conn = boto.connect_ec2(access_cred, secret_cred)
gladiator_image = conn.get_image('ami-89b779e0')
reservation = gladiator_image.run(min_count = count, max_count = count,
                                  user_data = user_data,
                                  instance_type='c1.medium', 
                                  key_name = 'MND_EC2_keypair',
                                  security_groups = ['MND_SSH'])
