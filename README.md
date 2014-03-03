

First time running notes
Currently I am unsure how to make beanstalkd, be installed correctly and what not, need to add it to bin. 
There are two ways of doing this, 

1) So instead before running make for the first time, or after the second time, added beanstalkd to [buildout] parts
it will probably fail, even if it does, it succeded, but not completely. After this remove beanstalkd from parts 
in buildout.cfg. beanstalkd will remain in var/parts
cd var/parts/beanstalkd
make
then start beanstalkd inside /var/parts/beanstalkd

2) Another way of adding beanstalkd, 
cd /var/parts
mkdir beanstalkd
cd beanstalkd
git clone git://github.com/kr/beanstalkd.git
cd beanstalkd
make
and then it can be started just like normal.
beanstalkd &


then need to create the database for django

./bin/django sql thunderdome
./bin/django syncdb
./bin/django is used for development where as production will be used for production


Addtionally certain config files need to have certain values set so the correct clients are pulled, referees know where the beanstalk is, etc.

These files are 
arena/thunderdome/config.py,

These two are only need for a production arena head environment.
aws_secrets.py - the amazon s3 information. 
secret_settings.py - this has the postgresql configs. 

