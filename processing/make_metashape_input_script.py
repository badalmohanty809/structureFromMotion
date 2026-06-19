# date: 19-06-2026
# author: MohantyB
# topic: historic aerial image processing
# description: script to create a metashape input script for each
#              directory in the metadata file. The script will create a
#              config file for each directory and a python script to
#              load the images into metashape. The config file will
#              contain the base path, dataset folder, output path,
#              project name, focal length, pixel size and the list of
#              images. The python script will read the config file and
#              load the images into metashape.


import os
import glob
import pandas as pd
from pathlib import Path


metadata_txt_file = r'D:\datasets\image_preprocessing\00_text_extraction\penarth_head_to_cold_knap\penarth_head_to_cold_knap_1_metadata.txt'
input_prt_dir = r'D:\datasets\image_preprocessing\04_add_padding\penarth_head_to_cold_knap'
out_dir = r'D:\datasets\metashape_input\penarth_head_to_cold_knap'

metadata_df = pd.read_csv(metadata_txt_file)
dir_list = metadata_df['dir'].to_list()


def build_metashape_script(config_filename):
    script_text = f"""
import Metashape
import os
# === READ CONFIG ===
script_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(script_dir, r"{config_filename}")
base_path = ""
dataset_folder = ""
output_path = ""
project_name = ""
focal_length = ""
pixel_size = ""
image_rel_paths = []
with open(config_file, 'r') as f:
    lines = f.readlines()
mode = None
for line in lines:
    line = line.strip()
    if not line:
        continue
    if line.startswith("base_path="):
        base_path = line.split("=", 1)[1]
    elif line.startswith("dataset_folder="):
        dataset_folder = line.split("=", 1)[1]
    elif line.startswith("output_path="):
        output_path = line.split("=", 1)[1]
    elif line.startswith("project_name="):
        project_name = line.split("=", 1)[1]
    elif line.startswith("focal_length="):
        focal_length = float(line.split("=", 1)[1])
    elif line.startswith("pixel_size="):
        pixel_size = float(line.split("=", 1)[1])
    elif line == "images:":
        mode = "images"
    elif mode == "images":
        image_rel_paths.append(line)
# === BUILD FULL PATHS ===
image_list = [
    os.path.join(base_path, dataset_folder, rel_path)
    for rel_path in image_rel_paths
]
# === METASHAPE ===
doc = Metashape.app.document
chunk = doc.chunk
chunk.label = "try_1"
chunk.addPhotos(image_list)
sensor = chunk.sensors[0]
sensor.focal_length = focal_length
sensor.pixel_size = (pixel_size, pixel_size)
sensor.fixed = True
# === SAVE ===
project_path = os.path.join(output_path, project_name)
doc.save(project_path)
"""
    return script_text



for dir_name in dir_list:
    print(f"Processing directory: {dir_name}")
    dir_path = os.path.join(input_prt_dir, dir_name)
    #  get all files in the directory andsubdirectories
    image_list = glob.glob(os.path.join(dir_path, '**', '*.tif'), recursive=True) + glob.glob(os.path.join(dir_path, '**', '*.tiff'), recursive=True)
    focal_len_in = metadata_df.loc[metadata_df['dir'] == dir_name, 'focal_ln_in'].values[0]
    #  convert to mm
    focal_len_mm = focal_len_in * 25.4
    dpi = metadata_df.loc[metadata_df['dir'] == dir_name, 'dpi'].values[0]
    p_size_mm = 25.4 / dpi
    py_file_name = os.path.join(out_dir, f"metashape_load_{dir_name}.py")
    # project_name = os.path.join(out_dir, f"metashape_{dir_name}.psx")
    config_file = os.path.join(out_dir, f"config_{dir_name}.txt")
    #  if config file exists, remove it
    if os.path.exists(config_file):
        os.remove(config_file)
    #  if py file exists, remove it
    if os.path.exists(py_file_name):
        os.remove(py_file_name)
    with open(config_file, "w") as f:
        f.write(f"base_path={input_prt_dir}\n")
        f.write(f"dataset_folder={dir_name}\n")
        f.write(f"output_path={out_dir}\n")
        f.write(f"project_name=metashape_{dir_name}.psx\n")
        if focal_len_in == -1:
            print(f"Warning: focal length for directory {dir_name} is -1.")
            f.write(f"focal_length=508\n") # assuming 20 inch focal length
        else:
            f.write(f"focal_length={focal_len_mm}\n")
        if dpi == -1:
                print(f"Warning: DPI for directory {dir_name} is -1.")
                f.write(f"pixel_size=0.028\n") # assuming 800 DPI
        else:
            f.write(f"pixel_size={p_size_mm}\n")
        f.write("images:\n")
        for img in image_list:
            rel_path = os.path.relpath(img, os.path.join(input_prt_dir, dir_name))
            f.write(rel_path + "\n")
    script_text = build_metashape_script(config_file.split("\\")[-1])
    output_py_file = Path(py_file_name)
    output_py_file.write_text(script_text, encoding="utf-8")
