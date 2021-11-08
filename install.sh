#! /bin/sh
 
echo "installing python virtual environment"
#python3 -m venv env
#source env/bin/activate

echo "installing python packages in virtual environment"
#pip install -r requirements.txt
deactivate

echo "Creating scripts to launch in virtual environment"

for f in *.py
do
parent_path=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
echo "#! /bin/sh
$parent_path/env/bin/python3 furk.py
" > ${f::-2}.sh
done

chmod +x *.sh

