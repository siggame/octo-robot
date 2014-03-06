

First time running notes
beanstalkd is need for running the arena head node, this gets cloned into var/parts/beanstalkd, but needs to be compiled. 

so after make finishes,
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

