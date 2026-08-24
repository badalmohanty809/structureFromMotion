


br_file_path=$1
hist_eq_file_path=$2
hist_eq_dir=$3
hist_eq_script_name=$4
script_dir=$5


if [ -f "$hist_eq_file_path" ]; then
    echo "File $hist_eq_file_path already exists. exiting."
    exit 0
fi

echo "Running histogram equalisation script: $hist_eq_script_name"

python "$script_dir/$hist_eq_script_name" "$br_file_path" "$hist_eq_file_path"
