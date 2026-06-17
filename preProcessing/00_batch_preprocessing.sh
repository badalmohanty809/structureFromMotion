

scrpit_dir="C:/Users/c25045127/OneDrive - Cardiff University/data_analysis/structureFromMotion/preProcessing/"
remove_broder_script_name=""
hist_eq_script_name="enhance_input_image.py"
add_padding_script_name="add_padding_to_image.py"

dir_txt="D:/datasets/image_preprocessing/01_remove_border/penarth_head_to_cold_knap/penarth_head_to_cold_knap_1.txt"

original_data_prt_dir="D:/datasets/image_preprocessing/01_remove_border/penarth_head_to_cold_knap/"
remove_border_prt_dir="D:/datasets/image_preprocessing/01_remove_border/penarth_head_to_cold_knap/"
hist_eq_prt_dir="D:/datasets/image_preprocessing/02_histogram_equalisation/penarth_head_to_cold_knap/"
add_padding_prt_dir="D:/datasets/image_preprocessing/04_add_padding/penarth_head_to_cold_knap/"

for dir in $(cat $dir_txt); do
    echo "Processing folder: $dir"
    original_data_dir="$original_data_prt_dir$dir/"
    echo "Original data folder: $original_data_dir"
    # check if the folder exists
    if [ ! -d "$original_data_dir" ]; then
        echo "Folder $original_data_dir does not exist. Skipping."
        continue
    fi
    find "$original_data_dir" -type f | while read in_file; do
        echo "Processing file: $in_file"

        #  run remove broder script
        if [[ "$in_file" == *br* ]]; then
            echo "File $in_file already has '_br' in its name."
            br_file_path="$in_file"
        else
            br_file_path="${in_file%.*}_br.${in_file##*.}"
            br_file_path="${br_file_path/$original_data_dir/$remove_border_prt_dir$dir/}"
            remove_border_dir="$(dirname "$br_file_path")"
            echo "Running remove border script: $remove_broder_script_name"
            echo "remove border output file: $br_file_path"
            if [ ! -d "$remove_border_dir" ]; then
                mkdir -p "$remove_border_dir"
            fi
            bash "$scrpit_dir/01_remove_border.sh" "$in_file" "$br_file_path" "$remove_border_dir" "$remove_broder_script_name" "$scrpit_dir"
        fi

        # run histogram equalisation script
        hist_eq_file_path="${br_file_path%.*}_clahe.${br_file_path##*.}"
        hist_eq_file_path="${hist_eq_file_path/$original_data_dir/$hist_eq_prt_dir$dir/}"
        hist_eq_dir="$(dirname "$hist_eq_file_path")"
        echo "histogram equalisation output file: $hist_eq_file_path"
        if [ ! -d "$hist_eq_dir" ]; then
            mkdir -p "$hist_eq_dir"
        fi
        bash "$scrpit_dir/02_histogram_equalisation.sh" "$br_file_path" "$hist_eq_file_path" "$hist_eq_dir" "$hist_eq_script_name" "$scrpit_dir"
    done

    # check the maximum width and height of the images in the histogram equalisation folder
    echo "Checking maximum width and height of images in: $hist_eq_prt_dir$dir/"

    max_width=0
    max_height=0
    while IFS= read -r in_file; do
        echo "Checking image size for: $in_file"
        read w h < <(gdalinfo "$in_file" | grep "Size is" | awk '{print $3, $4}' | sed 's/,//')
        [ -z "$w" ] && continue
        if [ "$w" -gt "$max_width" ]; then
            max_width=$w
        fi
        if [ "$h" -gt "$max_height" ]; then
            max_height=$h
        fi
    done < <(find "$hist_eq_prt_dir$dir/" -type f \( -iname "*.tif" -o -iname "*.tiff" \))

    echo "Max width: $max_width, Max height: $max_height"
    # save these values to a text file
    echo "$max_width,$max_height" > "$hist_eq_prt_dir$dir/max_width_height.txt"

    hist_eq_dir="$hist_eq_prt_dir$dir/"
    find "$hist_eq_dir" -type f \( -iname "*.tif" -o -iname "*.tiff" \) | while read -r hist_eq_file_path; do
        echo "Processing file: $hist_eq_file_path"

        # run add padding script
        add_padding_file_path="${hist_eq_file_path%.*}_padded.${hist_eq_file_path##*.}"
        add_padding_file_path="${add_padding_file_path/$hist_eq_dir/$add_padding_prt_dir$dir/}"
        add_padding_dir="$(dirname "$add_padding_file_path")"
        echo "add padding output file: $add_padding_file_path"
        if [ ! -d "$add_padding_dir" ]; then
            mkdir -p "$add_padding_dir"
        fi
        # echo "Running add padding script: $add_padding_script_name"
        bash "$scrpit_dir/04_add_padding.sh" "$hist_eq_file_path" "$add_padding_file_path" "$add_padding_dir" "$add_padding_script_name" "$scrpit_dir" "$hist_eq_prt_dir$dir/max_width_height.txt"
    done
done


# dir="1946_4654"
# in_file="D:/datasets/image_preprocessing/01_remove_border/penarth_head_to_cold_knap/1946_4654/3000s/CPE_UK_1871_3003.tif"
# 1944_4001