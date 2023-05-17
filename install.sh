#! /bin/bash

parent_path=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ) 
echo "installing python virtual environment"
cd $parent_path
python3 -m venv env
source env/bin/activate

echo "installing python packages in virtual environment"
pip install -r $parent_path/requirements.txt
deactivate

echo "Creating scripts to launch in virtual environment"

for f in *.py
do
if [[ $f == "configs.py" ]]; then
continue
fi
echo "#! /bin/sh
source $parent_path/env/bin/activate
$parent_path/$f \$1 \$2 \$3
" > $parent_path/${f::-2}sh
done

chmod +x *.sh
