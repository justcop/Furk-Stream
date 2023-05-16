#! /bin/bash

parent_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
env_dir="$parent_path/env"
requirements_file="$parent_path/requirements.txt"
new_requirements_file="$parent_path/requirements_new.txt"

echo "Checking if environment exists..."

if [ ! -d "$env_dir" ]; then
    echo "Installing Python virtual environment"
    cd "$parent_path"
    python3 -m venv env
    source env/bin/activate
else
    echo "Environment already exists. Skipping installation."
fi

echo "Checking for updated requirements..."

if [ -f "$requirements_file" ]; then
    rm "$new_requirements_file" 2>/dev/null
    touch "$new_requirements_file"
    for f in *.py; do
        if [[ $f == "configs.py" ]]; then
            continue
        fi
        echo "Processing $f"
        python -c "import ast; [print(l.split(' ')[1].split('=')[0]) for l in ast.parse(open('$f').read()).body if isinstance(l, ast.Import) or isinstance(l, ast.ImportFrom)]" >>"$new_requirements_file"
    done
    if cmp -s "$requirements_file" "$new_requirements_file"; then
        echo "No changes detected in requirements."
        rm "$new_requirements_file"
    else
        echo "Installing Python packages from updated requirements..."
        mv "$new_requirements_file" "$requirements_file"
        pip install -r "$requirements_file"
    fi
else
    echo "Generating initial requirements..."
    touch "$requirements_file"
    for f in *.py; do
        if [[ $f == "configs.py" ]]; then
            continue
        fi
        echo "Processing $f"
        python -c "import ast; [print(l.split(' ')[1].split('=')[0]) for l in ast.parse(open('$f').read()).body if isinstance(l, ast.Import) or isinstance(l, ast.ImportFrom)]" >>"$requirements_file"
    done
    echo "Installing Python packages from initial requirements..."
    pip install -r "$requirements_file"
fi

echo "Creating scripts to launch in virtual environment"

for f in *.py; do
    if [[ $f == "configs.py" ]]; then
        continue
    fi
    echo "#! /bin/sh
source $env_dir/bin/activate
$parent_path/$f \$1 \$2 \$3
" >"$parent_path/${f::-2}sh"
done

chmod +x *.sh
