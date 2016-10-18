#Octo-Robot

![{octo-robot}](http://i.imgur.com/fXvKgah.jpg)


How to run the arena (Ubuntu 14.04 - 15.10)

These will be very specific instructions on how to setup the arena for an actual tournament. There might be some slight differences when running this as a "test" arena, but those are typically for either convenience or pertain to other parts that are not functional before MegaminerAI starts. For testing and development, replace 'production' with 'development' in all commands.

This will assume some basic information about linux, and git. 
All testing and development for the arena is currently being done in a linux environment, the current arena nodes are using Ubuntu 14.04.5. (these should get upgraded to 16.X)
If you do not know about git or wish to learn more about it I would suggest visiting try.github.com along with git-scm.com/documentation

All steps will be done via terminal. Additionally I will refer to the base folder, octo-robot, as home directory.

To start off lets make sure everything is up to date.

```
sudo apt-get update
sudo apt-get upgrade
```

1) Generate an SSH key for Github

This link should tell you everything you need to do:

https://help.github.com/articles/generating-ssh-keys/

2) Install all necessary libraries. Install all of these on the head node and the gladiators.

```
sudo apt-get install libpq-dev python-dev libyaml-dev 
sudo apt-get install postgresql postgresql-contrib flex
sudo apt-get install python-pip libffi-dev python-beanstalkc 
sudo apt-get install python-boto python-yaml libcurl4-openssl-dev
sudo pip install cffi
```

The webserver that is currently used is called nginx, make sure to install it with

```
sudo apt-get install nginx
```

For the Javascript client you will need:

Node.js:

```
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.31.4/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install 6.4.0
```

For the Lua client you will need:

```
sudo apt-get install lua5.1 luajit lua-socket
```

For the Java client you will need:

```
sudo apt-get install openjdk-7-jdk maven
```

For the C++ client you will need:

```
sudo apt-get install libboost-all-dev cmake
```

For the C# client you need:

Lastest version of Mono, but Ubuntu default is out of date, so:

```
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
echo "deb http://download.mono-project.com/repo/debian wheezy main" | sudo tee /etc/apt/sources.list.d/mono-xamarin.list
sudo apt-get update
echo "deb http://download.mono-project.com/repo/debian wheezy-apache24-compat main" | sudo tee -a /etc/apt/sources.list.d/mono-xamarin.list
sudo apt-get install mono-devel mono-complete referenceassemblies-pcl ca-certificates-mono
```

You need git so you can interface with GitHub

```
sudo apt-get install git
```

3) Clone the arena directory

```
git clone git@github.com:siggame/octo-robot.git
```

4) build the arena

```
cd octo-robot
make
```

this will setup the project file for using a postgresql db

using `make develop` instead will setup the arena for using a sqlitedb, this can be useful and easier to setup than the postgresdb. 


5) Database setup

If in step 4 you ran `make develop` then skip this step and procede to step 6. 

Next the arena's database will need to be setup. This is a somewhat intense task as it requires setting up a postgres database. 

We need to switch over to the postgres user and preform the database setup. Everything in quotes will be the name of what it was used to create. I suggest using a different name when setting up the arena 

```
sudo su - postgres
createdb "arena_test_db"
createuser "arena_test_user" -P
```

You'll be prompted for a password for a new role. Do record or make note of the password.

```
exit
```

6) Database Initilization (django 1.8)

In the folder arena/settings is a file named production.py, this file will need to have the database information provided above.
For production you'll need to edit the "ENGINE" field to 'django.db.backends.postgresql_psycopg2' where as for testing, you'll need to change "ENGINE" to be 'django.db.backends.sqlite3'. 
For testing the file is instead called developement.py and should have all the required information already provided. 

The other fields will have the information passed to the production.py file from a file named secret_settings.py. The secret_settings file should also be in the arena/settings folder. If the secret_settings folder is missing then run `./bin/production` and the secret_settings.py file should be generated. If you are doing testing the file might be called `./bin/development` instead

After which open the secret_settings.py file in arena/settings folder and add in the postgres name, db the user and password. The postgres name should be equal to the database name that was used in the `createdb` command. This change is not necessary when make develop is used in step 4, make develop doesn't use secret settings. You should now be good to go on generating the database schema.

cd back to the base project directory, octo-robot

```
./bin/production makemigrations thunderdome
./bin/production migrate
./bin/production createsuperuser
```

You should get a prompt asking for information about setting up a test user.
Fill all that information in.
should be like user name, email and password its all for the admin account of the django website. 

These steps are for running the database the very first time. If changes to the models in the thunderdome or app, you'll have to run the `migrate` appname command. These command will change depending on the django version

I highly suggest reading the django tutorial where it goes through making a small application for doing polls/questions. Just note that where they use python manage.py you'll use either ./bin/development or ./bin/production depending on which you are doing. 


7) Configure the Arena

Now that the database is up and the schema is set the arena will need some clients. This is currently the hardest part of setting up a test arena, as the website that provides clients to the arena is usually down during non MegaMinerAI times. Most of the production stuff should be setup as the default is to reach out the website and look for clients. This is all done based on the name of the game. The arena has some config settings that define what game it should be playing, what game clients to look for etc. These are stored in models / fixtures ArenaConfig.

There are some past configs that are available for the purpose of running old games / as an example for setting future configs settings. To load these old configs run.

```
./bin/production loaddata arena/fixtures/configs.json
```

The selected config is denoted by which one is "active" check the database looking for which config is "active" if its not the one your look for it, switch that one to be the active one.

8) Checking out the website.

Production, o god this is complicated and requires setting up nginx and blah blah


nginx is complicated and is not in the scope of explination of this document, thus I point you to the nginx website and some if its documentation. The main nginx website is located at https://www.nginx.com and a beginners guide is located at http://nginx.org/en/docs/beginners_guide.html. I would highly suggest reading the beginners guide.

The main gist of nginx is that it is a process that should be running continuously that when someone types into the url of a web browser the webserver will process the requested link and return some data back.

After installing nginx a config file will have to be made to let nginx know what/where you've located the website that it will need to serve. These files are typically stored in /etc/nginx/sites-available, but then require a system link to the folder /etc/nginx/site-enabled. See end of step 14 for more details.

Testing

Procced to the root directory, octo-robot, and run the command `./bin/development runserver` This will set it up on 127.0.0.1:8000. I am running this in a vm so I choose to run it like `./bin/development runserver 0.0.0.0:8000` then I can access the website via my host machine. 

Then go to the website 127.0.0.1:8000/admin.
This is the base url of the admin site that django provides. Here you'll need to enter the username and password that was provided in step 5. Then type go to 127.0.0.1:8000/mies/thunderdome, the site itself is very minimal. Click on the Settings button on the top left, above Scoreboard. On here you should see a Currently Active Settings, Select a config and an Available settings display.

Create a new setting:

To do this run
```
./bin/production shell
```

This opens an interactive python shell with all the correct module imports and proper paths set.

run

```
from thunderdome.models import ArenaConfig
active_config = ArenaConfig.objects.get(active=True)
active_config.active = False 
active_config.save()

new_config = ArenaConfig()
new_config.name = "new_config"
new_config.game_name = "megaminerai-##-specific-name"
new_config.active = True
```

There are a few other parameters that can also be important depending on what you are doing, such as

```
new_config.beanstalk_host ('= "localhost"' for testing)
new_config.client_prefix ('= "git@github.com:"' for testing)
new_config.api_url_template
```

All of those are specific to what your setup looks like.

The beanstalk_host refers what ip the beanstalkd process is running, (the beanstalkd will be explained later TODO add step number). Client prefix refers to the server location of where the git clients are stored. Typically they will be on the webserver, but for testing it most likely be github take a look at the testing_plants arena settings to get an idea for how the client prefix looks. I think currently its like git@github.com: the api_url_template is specific to the production and has to do with updating the clients. 

In production the game name will be specific to what ever the website team comes up with, hopefully you can show this to them and they'll know what you are asking for, I believe they call it the game name slug

After you are happy with the configuration, you'll need to save the model.

To do this type in

```
new_config.save()
```

9) Get some test clients
   - Aow that the database is up the arena will need some clients
   - There is a file with some fake Spiders clients for testing purposes, 
   - This file can be located at https://gist.githubusercontent.com/Daniel17sep/3b149607b25fa6d25411e35bb3d31cc8/raw/3ae6b1e1867cc077facd31eafa1ece3f22aa41af/Spiders_Test.txt
   - You can also make your own using whatever clients you like, just follow the format in test file
   - All that needs to be down now is to run `./bin/python masterblaster/utilities/update_clients_from_gist.py `and pass the url as parameter. 
   
9) Get some real clients
   - If setting up for an actual arena run, the arena will get the information from the webserver instead of a test file. 
   - this is done as a multistep process. 
    a) First obtain a user name and password from the webserver and enter them into the secret settings file. 
    b) After which then you'll need to update the game name information and make sure the webserver url is correct. These are located in the arena/thunderdome/config.py file, 
       - replace game_name with the game name type, this would be obtained from the webserver team, 
       - same with client_prefix and api_url_template

10) Start the beanstalkc

```
cd octo-robot/var/parts/beanstalkd/
make
./beanstalkd
```

   This will start the beanstalkc deamon process that will do all the message passing between the different processes, this will start the process in the background and shouldn't involve anything else. If there is some error message like port is already binded or something then you'll need to figure out which program is the port specified then procceed to stop it then restart the beanstalkd process. 

11) Start the scheduler 

```
cd octo-robot
./bin/python masterblaster/scheduler_arena.py (For testing)
./bin/python masterblaster/scheduler_window_swiss.py (For realz)
```

Afterwhich the scheduler will use a whole terminal so create a new one

12) Start the archiver

```
cd octo-robot
./bin/python masterblaster/smart_archiver.py
```

At this point the entire headnode should be setup, and all that is left is to create the gladiators to start playing the games. 
Additionally there should be several games already scheduled, and some output on the scheduler indicating this. 

13) Start a gladiator. 
   - There is a file called generate_gladiator_package.py, this file was created to easy the difficulty of starting a gladiator. Normally one would have to download the server, and tar the server files and the files in the gladiator folder, this should do that for you you'll just need to pass in the parameter for where to find the MegaMinerAI repository that you'll want the server from.

```
cd octo-robot
./bin/python masterblaster/generate_gladiator_package.py Cerveau
```
   
For development work all that is then needed is to change the path for living_corders in the spinup_local_gladiator.py file then 

```
./bin/python masterblaster/spinup_local_gladiator.py
```

This will create a replica of what a real gladiator would have. 
then one can go into the living_corders directory and 

```
bash ./kick.sh
```

which will spinup a gladiator, which will then should begin runnning games. 
    
For actual running the arena its a bit more complicated. 
The folder that the generate_gladiator_package creates will have to be targed as a tgz
Afterwhich the tar file has to be placed into the gladiator folder which may or may not exist in the static folder.
Thus you should have var/static/gladiator/<tar_file>
Then you'll need to make sure that you have nginx all configured to use that folder as its static folder to serve files. 
Then you'll have to start the nginx process by 
 
 - The file in /etc/nginx/sites-enabled (probably `arena` or something):
      Should look something like this:
         
         # -*- mode: nginx -*-
         
         upstream gunicorn {
           server localhost:8000 fail_timeout=0;
         }
         
         server {
           listen 80;
           listen 8080;
           server_name 50.17.162.7;
           root /user/share/nginx/www;
         
           client_max_body_size 0;
         
           location /gladiator {
             root /home/ubuntu/octo-robot/var/static;
             autoindex on;
             try_files $uri $uri/ 404;
           }
         
           location @gunicorn {
             client_max_body_size 0;
             proxy_pass http://gunicorn;
             proxy_redirect off;
             proxy_read_timeout 5m;
             proxy_set_header Host        $host;
             proxy_set_header X-Real-IP   $remote_addr;
             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             add_header 'Access-Control-Allow-Origin' 'http://vis.megaminerai.com';
           }
         
           location / {
             try_files $uri @gunicorn;
           }
         }
         
 - cd octo-robot
 - `sudo service nginx restart`
 - `./bin/gunicorn --workers=<like 1.5 x number of cores on head node> arena.arena_wsgi:application`
 
After which the gladiators can be started, 
    - using `./bin/python masterblaster/spinup_arena_instance` (use --help to figure out what params you need). 
These instructions have pretty much all assumed you are using the amazon ec2 instances, and have setup the proper permissions and have entered the correct keys and user names. 

14) Monitoring 
   - At this point he arena should be running and you'll just have to do monitoring.
