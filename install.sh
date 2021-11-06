#! /bin/bash

echo "installing python virtual environment"
python3 -m venv env
source env/bin/activate

echo "installing python packages in virtual environment"
pip install -r requirements.txt
deactivate
set –o noclobber

echo "Creating scripts to launch in virtual environment"

echo "#!/bin/bash                                                                                   
parent_path=$( cd \"$(dirname \"${BASH_SOURCE[0]}\")\" ; pwd -P )                                  
cd \"$parent_path\"                                                                              
./env/bin/python3 furk.py" > furk.sh
echo "#!/bin/bash                                                                                   
parent_path=$( cd \"$(dirname \"${BASH_SOURCE[0]}\")\" ; pwd -P )                                  
cd \"$parent_path\"                                                                              
./env/bin/python3 linker.sh" > linker.sh
echo "#!/bin/bash                                                                                   
parent_path=$( cd \"$(dirname \"${BASH_SOURCE[0]}\")\" ; pwd -P )                                  
cd \"$parent_path\"                                                                              
./env/bin/python3 strmFromFurkURL.sh" > strmFromFurkURL.sh
chmod +x furk.sh
chmod +x linker.sh
chmod +x strmFromFurkURL.sh
set +o noclobber
