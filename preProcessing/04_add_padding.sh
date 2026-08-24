

hist_eq_file_path=$1
add_padding_file_path=$2
add_padding_dir=$3
add_padding_script_name=$4
script_dir=$5
max_width_height_file=$6


if [ -f "$add_padding_file_path" ]; then
    echo "File $add_padding_file_path already exists. exiting."
    exit 0
fi

echo "Running add padding script: $add_padding_script_name"

python "$script_dir/$add_padding_script_name" "$hist_eq_file_path" "$add_padding_file_path" "$max_width_height_file"
