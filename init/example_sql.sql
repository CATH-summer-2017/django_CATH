

#### This CREATEs a new MySQL user named "django" with password as "Django_passw0rd"
CREATE USER "django"@"localhost" IDENTIFIED BY "Django_passw0rd";

#### This CREATEs a separate SQL DATABASE named "django"
CREATE DATABASE django CHARACTER SET utf8;  

#### This GRANTs appropriate privileges to the user "django"@"localhost"
GRANT ALL PRIVILEGES on django.* TO "django"@"localhost" ;




#### CREATE more DATABASEs and GRANT correct privileges
CREATE DATABASE mtest_django character set utf8;
GRANT ALL PRIVILEGES on mtest_django.* to 'django'@'localhost';

CREATE DATABASE test_django character set utf8;
GRANT ALL PRIVILEGES on test_django.* to 'django'@'localhost';



##### Alternatively you can grant all privileges to "django" (not safe)
-- GRANT ALL PRIVILEGES ON * . * TO 'django'@'localhost';
