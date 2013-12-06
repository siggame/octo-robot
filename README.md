

First time running notes
Currently I am unsure how to make beanstalkd, be installed correctly and what not, need to add it to bin. 
So instead before running make for the first time, or after the second time, added beanstalkd to [buildout] parts
it will probably fail, even if it does, it succeded, but not completely. After this remove beanstalkd from parts 
in buildout.cfg. beanstalkd will remain in var/parts
cd var/parts/beanstalkd
make
then start beanstalkd inside /var/parts/beanstalkd

then need to create the database for django

./bin/django sql thunderdome
./bin/django syncdb
./bin/django is used for development where as production will be used for production
