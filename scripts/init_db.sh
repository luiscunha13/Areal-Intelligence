#!/bin/bash
# Creates both the app database and the Airflow database on first init
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE arealdb' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'arealdb')\gexec
    SELECT 'CREATE DATABASE airflow' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec
    CREATE USER airflow WITH PASSWORD 'airflow';
    GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
    ALTER DATABASE airflow OWNER TO airflow;
EOSQL

# Enable TimescaleDB on the app database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname arealdb <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
EOSQL

