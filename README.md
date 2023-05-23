# Log Severity Level Processor

# Application Documentation

This tutorial is organized as follows:

- [How to prepare your environment to develop](#markdown-header-how-to-prepare-your-environment-to-develop)

- [How to run Django application in VS Code](#markdown-header-how-to-run-django-application-in-vs-code)

- [How to generate docker images and deploy locally](#markdown-header-how-to-generate-docker-images-and-deploy-locally)

---

## How to prepare your environment to develop

For local development using VSCode we need to set up our environment.

Basic Requirements:

- Python 3.7.5

- Docker

- VSCode

- PostgreSQL (required by Django)

- srcML (https://www.srcml.org/)

Requirements python for application:

- requirements.txt

Creating the Development Environment:

To setup our development environment, we will use python's virtualenv. For that, you need to have python version 3.7 installed on my machine, to check the python version type:

```
python --version
```

Inside the root folder of this repository, run the following command to create the virtualenv.

```
python -m venv venv
```

To activate the virtual environment run the command below:

- On Windows:
```
.\venv\Scripts\activate
```

- On Mac/Linux:
```
source venv/bin/activate
```

After, we need to update pip tool:

```
python -m pip install --upgrade pip
```

Now, you are in the python virtual environment with pip up to date. Install the requirements using the commands below. You have to run the commands from the root folder of this repository.

```
pip install -r requirements.txt
```

*Optional:* when you want to deactivate virtualenv type the command below:

```
deactivate
```

---

## How to run Django application in VS Code:

After has been set up the Venv, you can start develop in VS Code.

In the first execution, you have to setup the application. Change to /log/app folder.

### 1. Copy the config/.env_example file to config/.env:

- On Windows:
```
copy config\.env_example config\.env
```

- On Mac/Linux:
```
cp config/.env_example config/.env
```

### 2. Edit environment variables:

This step is optional. You can edit the file `.env` using the text editor of your choice.

- On Windows:
```
DEBUG=ON
GIT_CLONE_PATH=C:\repositories\
DATABASE_URL=psql://postgres:postgres@localhost:5432/log
ALLOWED_HOSTS=localhost
STATIC_ROOT=static/
STATIC_URL=/static/
DJANGO_LOG_DIR=log/
LOG_FILENAME=slogminer.log
```

- On Mac/Linux:
```
DEBUG=ON
GIT_CLONE_PATH=/home/repositories/
DATABASE_URL=psql://postgres:postgres@localhost:5432/log
ALLOWED_HOSTS=localhost
STATIC_ROOT=static/
STATIC_URL=/static/
DJANGO_LOG_DIR=log/
LOG_FILENAME=slogminer.log
```

Change the credentials for accessing Postgres. they are located in `app/config/.env`.

### 3. Create database structure:

Make sure the PostgreSQL service is running. You first need to create a database on the local server called `log`. Then, run:

```
python .\manage.py migrate
```

### 4. Create a new admin user

Usually we use the user *admin* and the password as well *admin* in development environment, for tests purposes only. The email field we let empty.
*Please, do not use this in production.*

```
python .\manage.py createsuperuser
```

### 5. Run the application:

```
python .\manage.py runserver
```

For the other executions, you do not have to create admin user, because the database will be already created inside your local application folder.
You just need to run *runserver* command.

But, if you re-clone the repository or delete the database, you have to re-run this sequence again.

Eventually, you will have to run *makemigrations* and *migrate* commands again to update the database.

---

## Django commands:

Execute the commands sequentially to complete the database with the data needed for the search:

```
python manage.py clone_repositories
python manage.py statements_pipeline
python manage.py metaatribute_pipeline
python manage.py syntax_pipeline
python manage.py integration_pipeline
python manage.py branchcomparison_pipeline
```

---

## Git Commands from clone repositories (optional):

Attention: You need to create a folder called "repositories" inside the program folder and clone the repositories inside this folder.

To create the directory you can use the command below under Linux or MacOS:

```
mkdir repositories
```

For better organization clone the repositories informing the folder with the system name and version.

```
git clone -b release-3.0.0-RC0 --single-branch https://github.com/apache/hadoop.git hadoop-3.0.0-RC0
git clone -b release-3.3.3-RC1 --single-branch https://github.com/apache/hadoop.git hadoop-3.3.3-RC1
```

## Enabling Windows Long Path

To clone some java repositories on windows, it is necessary to activate the function that allows windows to read files with a path longer than 255 characters.

https://www.microfocus.com/documentation/filr/filr-4/filr-desktop/t47bx2ogpfz7.html

or

https://www.thewindowsclub.com/how-to-enable-or-disable-win32-long-paths-in-windows-11-10

And run this command as administrator:

```
git config --system core.longpaths true
```

## Command to update the UML chart

```
python manage.py graph_models -a -o log_severity_level_processor.png
``` 

## Using command line to execute funtions

The functions to clone and process repositories can be now executed directly from the command line.

The system should already be registered before the command in the terminal. 

To perform the function for a particular system/branch, optional arguments --system and --branch can be added, followed by their respective value.s
If these areguments are not passed, the system executes the command for all the existing systems.
```
python manage.py clone_repositories 
python manage.py clone_repositories --system Hadoop
python manage.py clone_repositories --system Hadoop --branch release-3.3.3-RC1
```

## How to generate docker images and deploy locally

We will show you how to generate docker images and deploy the docker container locally. 

To build the application and generate docker images you have to execute the command bellow. Execute from root folder (/log).

```
docker-compose build
```

To deploy the application locally, you have to have execute following command:

```
docker-compose up -d
```

*Tip: if you are in Windows, open a Powershell prompt to run Docker. Do not run inside VS Code prompt because it does not manage memory very well.*

It will set up the docker container from docker image and create the volumes to store application database and data files.

After, we install static artifacts in application. For this, execute:

```
docker-compose exec app python3 /app/manage.py collectstatic --noinput
```

Usually we use the user *admin* and the password as well *admin* in development environment, for tests purposes only. The email field we let empty.
*Please, do not use this in production.*

```
docker-compose exec app python3 /app/manage.py createsuperuser
```

After, we create the database:

```
docker-compose exec app psql -U postgres -h db -c 'CREATE DATABASE log;'
```

After, we apply the database structure:

```
docker-compose exec app python3 /app/manage.py migrate
```

Then we will clone repositories:

```
docker-compose exec app python3 /app/manage.py clone_repositories
```

Then we will run the pipelines:

```
docker-compose exec app python3 /app/manage.py statements_pipeline
docker-compose exec app python3 /app/manage.py metaatribute_pipeline
docker-compose exec app python3 /app/manage.py syntax_pipeline
docker-compose exec app python3 /app/manage.py integration_pipeline
```

After, create a new admin user. Usually we use the user *admin* and the password as well *admin* in development environment, for tests purposes only. The email field we let empty.
*Please, do not use this in production.*

```
docker-compose exec app python3 /app/manage.py createsuperuser
```

*Important:* this sequence is for the first docker deploy. If you do changes in the application code and need to re-deploy docker, just run *build* and *run* commands. The other commands will be not needed because the container will be already created and will already have the database.
However, eventually, we will need to run *makemigrations* and *migrate* to update the database.

*Optional:* if you want to stop execution of containers, execute the command:

```
docker-compose stop
```

*Optional:* if you want to remove containers, execute the command:

```
docker-compose down
```
