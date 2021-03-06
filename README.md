# SMRPO-scrum-app

Create postgres database (https://www.postgresql.org/)

```
CREATE DATABASE SMRPO_scrum_app WITH LC_COLLATE 'sl_SI.utf8' LC_CTYPE 'sl_SI.utf8' TEMPLATE template0;
CREATE USER scrum_admin WITH PASSWORD 'admin';

ALTER ROLE scrum_admin SET client_encoding TO 'utf8';
ALTER ROLE scrum_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE scrum_admin SET timezone TO 'UTC';
ALTER USER scrum_admin CREATEDB;

GRANT ALL PRIVILEGES ON DATABASE SMRPO_scrum_app TO scrum_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scrum_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scrum_admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO scrum_admin;
```
Install python 3.7
*python -m pip install Django
*pip install psycopg2 (adapter/driver for DB communication)