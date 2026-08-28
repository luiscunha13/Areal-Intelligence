#!/bin/bash
# Creates both the app database and the Airflow database on first init
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE arealdb;
    CREATE DATABASE airflow;
EOSQL

# Enable TimescaleDB on the app database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname arealdb <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
EOSQL
