#! /bin/sh
 
echo "installing python virtual environment"
python3 -m venv env
source env/bin/activate

echo "installing python packages in virtual environment"
pip install -r requirements.txt
deactivate

echo "Creating scripts to launch in virtual environment"

for f in *.py
do
echo "#! /bin/sh
$( cd ""\$(dirname ""\${BASH_SOURCE[0]}"")" ; pwd -P )/env/bin/python3 furk.py
" > ${f::-2}.sh
done

chmod +x *.sh

