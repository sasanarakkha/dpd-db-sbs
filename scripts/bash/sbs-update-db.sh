#!/bin/bash

# update dpd-db-sbs from github release

set -euo pipefail

echo "=== Cleaning dpd-db-sbs-old ==="
rm -rf /home/django/dpd-db-sbs-old

echo "=== Cloning new repository ==="
git clone --branch sbs-ru https://github.com/sasanarakkha/dpd-db-sbs.git dpd-db-sbs-new
cd dpd-db-sbs-new

echo "=== Downloading latest dpd.db.tar.bz2 ==="
wget https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/download/dpd.db.tar.bz2

echo "=== Extracting database ==="
tar -xvjf dpd.db.tar.bz2

echo "=== Copying existing env ==="
cp -r /home/django/dpd-db-sbs/env .

echo "=== Copying start script ==="
cp /home/django/dpd-db-sbs/start-uvicorn-fastapi.sh .

echo "=== Killing old main_ru:app process ==="
pkill -f "main_ru:app" || echo "No matching process found"

echo "Waiting 10 seconds to ensure shutdown…"
sleep 10

echo "=== Rotating directories ==="
mv /home/django/dpd-db-sbs /home/django/dpd-db-sbs-old
mv ~/dpd-db-sbs-new /home/django/dpd-db-sbs

echo "=== Starting new server ==="
cd /home/django/dpd-db-sbs
./start-uvicorn-fastapi.sh

echo "Waiting 10 seconds for server to start…"
sleep 10

echo "=== Running uvicorn processes ==="
ps -ef | grep uvicorn

echo "=== DONE ==="
