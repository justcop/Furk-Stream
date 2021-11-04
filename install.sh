#! /bin/bash

python3 -m venv env
source env/bin/activate
echo 'env' > .gitignore
pip install -r requirements.txt
deactivate
set –o noclobber
echo "./env/bin/python3" furk.py > furk.sh
echo "./env/bin/python3" linker.py > linker.sh
echo "./env/bin/python3" strmFromFurkURL.py > strmFromFurkURL.sh
set +o noclobber
