#! /bin/bash

python3 -m venv env
source env/bin/activate
echo ‘env' > .gitignore
pip install -r requirements.txt
deactivate
