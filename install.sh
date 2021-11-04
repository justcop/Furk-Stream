#! /bin/bash

echo "installing python virtual environment"
python3 -m venv env
source env/bin/activate

echo "installing python packages in virtual environment"
pip install -r requirements.txt
deactivate
set –o noclobber

echo "Creating scripts to launch in virtual environment"

echo "./env/bin/python3" furk.py > furk.sh
echo "./env/bin/python3" linker.py > linker.sh
echo "./env/bin/python3" strmFromFurkURL.py > strmFromFurkURL.sh
chmod +x furk.sh
chmod +x linker.sh
chmod +x strmFromFurkURL.sh
set +o noclobber
