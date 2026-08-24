

in_file=$1
br_file_path=$2
remove_border_dir=$3
remove_broder_script_name=$4
script_dir=$5

if [ -f "$br_file_path" ]; then
    echo "File $br_file_path already exists. exiting."
    exit 0
fi

mv "$in_file" "$br_file_path"
