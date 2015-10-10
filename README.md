
How to run the arena.
These will be very specific instructions on how to setup the arena for an actual tournament. There might be some slight differences when running this as a "test" arena, but those are typically for either convenience or pertain to other parts that are not functional before MegaminerAI starts. 

This will assume some basic information about linux, and git. 
All testing and development for the arena is currentlying being done in a linux environment, the current arena nodes are using some version of ubuntu, 12.04 I think. (these should get upgraded to 14.04)
If you do not know about git or wish to learn more about it I would suggest visiting try.github.com along with git-scm.com/documentation

All steps will be done via terminal. Additionally I will refer to the base folder, octo-robot, as home directory.


1) Clone the arena directory

`git clone git@github.com:siggame/octo-robot.git`

The arena uses buildout to download and install all the necessary python packages and libraries, so after the clone is complete 

`cd octo-robot`

Step 3 will require psycopg2 which is the python postgresql drivers which will require python-dev and postgres to be installed. 

3) make

Next the arena's database will need to be setup. This is a somewhat intense task as it requires setting up a postgres database. 
A perfect example that teaches one how to set this up step by step can be located at https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-django-with-postgres-nginx-and-gunicorn. That tutorial also includes setting up nginx and gunicorn which are also used for the arena's website component. Another thing to keep in mind about buildout is that it will create executables which will be used instead of any other executable instead of ones that are already on the system, it will create a python executable which will be used instead of the system provided python. 

You will only need to read steps 1 through 7 everything else will be explained. I would however suggest using a different database name and user name for the postgress database, but reguardless of what you use just remember to write it down somewhere as it will be used later. 

3.4 ish)

more or less exact command to complete setting up a postgres server 


sudo apt-get update && sudo apt-get upgrade && sudo apt-get install libpq-dev python-dev 
sudo apt-get install postgresql postgresql-contrib
These should install the nessasary libraries for postgres python will still need some required packages to interact with postgres
which should be satified by psycopg2, this should be covered by buildout

Now we'll need to build the database and the user

Everything in qoutes will be used as the name of what it was used for, but should be renamed when you are making the object

sudo su - postgres

should have postgres as the user name of who you are log in as, i.e. the first word on the far left of the terminal

createdb "arena_test_db"

createuser "arena_test_user" -P

You'll be prompted for a password for new role. make sure to remember the password.

exit

to logout from the postgres user

then you'll need to set the postgres user name, db name, and password in the secret file.

4) Configure the database connection. 
   - In the folder arena/settings is a file named production.py this file will need to have the database information.
       this information is passed in from a file named secret_settings.py
   - Change the fields "Engine" : to have 'django.db.backends.postgresql_psycopg2'


The secret file is located in teh settings folder, if the secret file does not exist then you'll need to atleast run
./bin/production

which will generate it for you.

after which open the secret_settings.py file in arena/settings folder and add int eh postgres name, db the user and password


should be good to go on generating the database scheme and getting the magic of the arena.

cd back to the base project directory, octo-robot

./bin/production sql thunderdome
./bin/production sql k_storage
./bin/production syncdb

You should get a prompt asking for information about setting up a test user.
Fill all that information in.
should be like user name, email and password its all for the admin account of the django website. 


(IGNORE STEP 5)
5) create the database
   - now that django knows where the database is, go into the home directory. 
   type ./bin/production migrate thunderdome
   this will create the database tables, if you are using a django version older than 1.7 then type ./bin/production sql thunderdome instead

6) Get some test clients
   - now that the database is up the arena will need some clients
   - I have created a fake clients file that will add in some clients for fake testing purposes, 
   - this file can be located at https://gist.github.com/brandonphelps/4d812a128e09bedec729
   - all that needs to be down now is to run the file masterblaster/utilities/update_clients_from_gist.py and pass the url as parameter. 
   

6) Get some real clients
   - If setting up for an actual arena run, the arena will get the information from the webserver instead of a test file. 
   - this is done as a multistep process. 
    a) First obtain a user name and password from the webserver and enter them into the secret settings file. 
    b) After which then you'll need to update the game name information and make sure the webserver url is correct. These are located in the arena/thunderdome/config.py file, 
       - replace game_name with the game name type, this would be obtained from the webserver team, 
       - same with client_prefix and api_url_template

7) Start the beanstalkc
   - cd octo-robot/var/parts/beanstalkd/
   - make
   - ./beanstalkd & 
   This will start the beanstalkc deamon process that will do all the message passing between the different processes


8) Start the scheduler 
   - cd octo-robot
   - ./bin/python masterblaster/scheduler_window_swiss.py
   
afterwhich the scheduler will use a whole terminal so create a new one

9) Start the archiver
   - cd octo-robot
   - ./bin/python masterblaster/smart_archiver.py

create another terminal 
At this point the entire headnode should be setup, and all that is left is to create the gladiators to start playing the games. 
Additionally there should be 5 games already scheduled, and some output on the scheduler indicating this. 

10) Start a gladiator. 
   - There is a file on the main branch called generate_gladiator_package.py, this file was created to easy the difficulty of starting a gladiator. Normally one would have to download the server, and tar the server files and the files in the gladiator folder, this should do that for you you'll just need to pass in the parameter for where to find the MegaMinerAI repository that you'll want the server from. 
    An example for MegaMinerAI11 is as such, 
    - cd octo-robot
    - ./bin/python masterblaster/generate_gladiator_package MegaMinerAI-11
    for development work all that is then needed is to change the path for living_corders in the spinup_local_gladiator.py file
    then ./bin/python masterblaster/spinup_local_gladiator.py
    This will create a replica of what a real gladiator would have. 
    then one can go into the living_corders directory and run the ./kick.sh file which will spinup a gladiator, which will then should begin runnning games. 
    
    For actual running the arena its a bit more complicated. 
    The folder that the generate_gladiator_package creates will have to be targed as a tgz
    Afterwhich the tar file has to be placed into the gladiator folder which may or may not exist in the static folder.
    Thus you should have static/gladiator/<tar_file>
    Then you'll need to make sure that you have nginx all configured to use that folder as its static folder to serve files. 
    Then you'll have to start the nginx process by 
    - cd octo-robot
    - ./bin/gunicorn arena.arena_wsgi:application
    After which the gladiators can be started, 
    - using ./bin/python masterblaster/spinup_arena_instance. 
    These instructions have pretty much all assumed you are using the amazon ec2 instances, and have setup the proper permissions and have entered the correct keys and user names. 


11) Monitoring 
   - At this point he arena should be running and you'll just have to do monitoring. 
