
First time doing development for arena
      
Using git to clone the repo.
Then cd into the repo. 
then type make develop
this will download and build a bunch of stuff, might take awhile.

then need to create the database for django

type 
./bin/development sql thunderdome
./bin/development syncdb

beanstalkd will need to be running, so next
cd /var/parts/beanstalkd
type make
then run ./beanstalkd

Then with this you can run the arena. 

The arena is going to need a bunch of clients to be running, since the webserver is down during non megaminer times,
there is a file that contains with a bunch of testing clients, located at https://gist.githubusercontent.com/brandonphelps/4d812a128e09bedec729/raw/89ef1c50330f0420f6fd2931a322551ba852f588/gistfile1.txt
This file can be used with so you can type
./bin/python masterblaster/utilities/update_clients_from_gist https://gist.githubusercontent.com/brandonphelps/4d812a128e09bedec729/raw/89ef1c50330f0420f6fd2931a322551ba852f588/gistfile1.txt

using this in combination with the gladiator/fake_ref.py one can run a mini-testing arena. 


The rest can be ignored for now. 

Addtionally certain config files need to have certain values set so the correct clients are pulled, referees know where the beanstalk is, etc.

These files are 
arena/thunderdome/config.py,

These two are only need for a production arena head environment.
aws_secrets.py - the amazon s3 information. 
secret_settings.py - this has the postgresql configs. 

