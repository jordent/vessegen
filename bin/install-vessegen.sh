#!/bin/bash

sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv python3-wheel python3-setuptools
python3 -m venv env
source env/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install .