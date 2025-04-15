#!/bin/bash
cd /home/read-manager
source venv/bin/activate
pip install -r requirements.txt
exec gunicorn -c gunicorn_config.py wsgi:app
