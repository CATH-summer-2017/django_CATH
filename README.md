
# django_CATH
[![Build Status](https://travis-ci.org/CATH-summer-2017/django_CATH.svg?branch=master)](https://travis-ci.org/CATH-summer-2017/django_CATH)

A data browser for the CATH database.

Check [`domchop`](https://github.com/CATH-summer-2017/domchop) (Especially the [wiki](https://github.com/CATH-summer-2017/domchop) page) and [CATH](http://www.cathdb.info) if you are new to the concept of Domchopping. 

Also check [wiki](https://github.com/CATH-summer-2017/django_CATH/wiki) of this repo for some background.

# Prerequisite
------
**Preferably you should start a virtual environment to keep everything trackable.**

### 1. Django > 1.8
You should have Django installed before installation.
Install Django with
```sh
pip install Django==1.11.* --user
```
If for whatever reason this fails, you may try `apt insatll python-django` but please do check the Django version is higher than 1.8. Or you can download .whl from [Django-1.11.4-py2.py3-none-any.whl](https://pypi.python.org/packages/fc/fb/01e0084061c50f1160c2db5565ff1c3d8d76f2a76f67cd282835ee64e04a/Django-1.11.4-py2.py3-none-any.whl#md5=71cf96f790b1e729c8c1a95304971341)  and do `wheel install Django-1.11.4-py2.py3-none-any.whl` .

###  2. MySQL
Django uses a SQL as its backend to store data. Django_CATH has been developed with MySQL but it is possible to switch to PostgreSQL or SQLite since [Django](https://docs.djangoproject.com/en/1.11/ref/settings/#databases) offers native support to these databases. 

##### INSTALLING MySQL

Install a local MySQL via
```sh
sudo apt-get install mysql-client
sudo apt-get install mysql-server
```

You might need this package on top of a working MySQL
```sh
sudo apt-get install libmysqlclient-dev
```

##### Configure MySQL

To setup Django_CATH, we need a running MySQL server to which Django_CATH can talk and make changes. It's advised to:
  * Create a separate SQL database for Django
  * Create a separate test database for Django
  * Create a separate SQL user for Django
  * Grant appropriate privileges to the SQL user for Django 

We show a MySQL example here:


```sql
#### This creates a separate SQL database named "django"
CREATE DATABASE "django" CHARACTER SET utf8;  

#### This creates a new MySQL user named "django" with password as "Django_passw0rd"
CREATE USER "django"@"localhost" IDENTIFIED BY "Django_passw0rd";

#### This grants appropriate privileges to the user "django"@"localhost"
GRANT ALL PRIVILEGES on django.* TO "django"@"localhost";

#### Create a separate test database and grant access to django
CREATE DATABASE "test_django" CHARACTER SET utf8;  
GRANT ALL PRIVILEGES on test_django.* TO "django"@"localhost";
```

It's also possible to exceute this MySQL statement in bash shell, although you will have to strip the quotes (" or ') off the MySQL command. (Remember to fill "{your username}" with "root" or whatever MySQL user with enough privilege):
```sh
mysql -u{your username} -p -e "CREATE DATABASE django CHARACTER SET utf8;"
```

##### Configure Django to use MySQL
The connection to SQL backend is stored in the ["init/django_settings.py"](https://github.com/CATH-summer-2017/django_CATH/blob/master/init/django_settings.py) (which will gets concatenated to "rootsite/rootsite/settings.py" to overwrite the default config.) We should edit this file accordingly to reflect the MySQL configuration, including:
  * "NAME": name of the database to be used by Django (e.g: "django" )
  * "USER","PASSWORD": credentials that will be used by Django to access the MySQL
  * "TEST":{"NAME"} : name of the test database to be used by Django (e.g: "test_django" )

# Compatibility
-----
Python: 2.7.0

# Installation
------

1. Ensure you have a working Django site.
  * If not, create one with
  ```sh
  django-admin startproject rootsite
  ```
2. clone this reposiory into your site dir ("rootsite") with the name "tst"
  ```sh
  git clone https://github.com/CATH-summer-2017/django_CATH.git rootsite/tst
  ```
3. Set environment variable $PDBlib to where you store your PDB's. Preferably add this line to your bash profile like '~/.bashrc'
  ```sh
  export PDBlib=$PWD/rootsite/tst/static/temppdbs   ### This is the PDB library that comes with the repository
  export SEQlib=$PWD/rootsite/tst/static/tempseqs   ### This is the PDB library that comes with the repository
  ```
4. Configure your database connection (MySQL) as [previously described](#configure-mysql) and edit ```init/django_settings.py``` [accordingly](#configure-django-to-use-mysql).

After editing the ```init/django_settings.py```, we concatenate it to the end of ```rootsite/rootsite/settings.py``` to overwrite the database settings. This should only be done by once, and any further modification should be made directly to ```rootsite/rootsite/settings.py```

```sh
cp rootsite/tst/init . -r
cat init/django_settings.py >> rootsite/rootsite/settings.py
cat init/django_urls.py >> rootsite/rootsite/urls.py     #### We also need to concatenate to overwrite the rootsite/urls.py
rm init -rf
```

5. Finally, install dependencies with:
```
pip install -r rootsite/tst/requirements.txt
```

6. Test your installation with:
```sh
cd rootsite
./manage.py migrate tst  #### create the SQL schema
./manage.py shell < tst/dbscript/initnodes.py   #### Init node tree from a S35 list
./manage.py shell < tst/dbscript/struct2S.py    #### Caculate structure-based statistics from structure in $PDBlib
./manage.py shell < tst/dbscript/S2H.py         #### Caculate hierarchial-based statistics
./manage.py dumpdata tst -o tst/fixtures/test_temp.json #### dump the database to be used in the test
./manage.py test tst --keepdb    #### run unittests

./manage.py runserver 0.0.0.0:8001 &   #### just testing the functionality of the server
```

Usage
------
* http://localhost:8001/tst/domain ### page contain werido domains
* http://localhost:8001/tst/superfamily ### page listing superfamilies
* http://localhost:8001/tst/superfamily/id/2.30.39.10 ### page listing a specifi superfamily
* To load pre-calculated datasets (stored in "fixtures/"), simply do:
```
./manage.py loaddata tst/fixtures/cathB-0728-DOPE_nbPCA.json
```
