

import os
import pandas as pd
import random
from itertools import product
import matplotlib
matplotlib.use("TkAgg")   # Interactive window
import matplotlib.pyplot as plt
from PIL import Image


def update_title():
    # DISPLAY CURRENT GCP
    global current_gcp, mode
    if current_gcp >= len(gcps):
        return
    title.set_text(
    f"Image: {image_path}\n"
    f"Current GCP: {gcps[current_gcp]}\n"
    f"Mode: {mode}\n\n"
    "m = mark point | 0 = not visible | u = undo"
    )
    fig.canvas.draw_idle()


def next_gcp():
    # NEXT GCP
    global current_gcp
    global mode
    current_gcp += 1
    mode = "navigate"
    if current_gcp >= len(gcps):
        print("\nFinished.\n")
        print("Results:")
        for row in results:
            print(row)
        plt.close(fig)
        return
    update_title()


def onclick(event):
    # CLICK EVENT
    global mode
    if mode != "mark":
        return
    if event.inaxes != ax:
        return
    if event.xdata is None or event.ydata is None:
        return
    x = int(round(event.xdata))
    y = int(round(event.ydata))
    gcp_name = gcps[current_gcp]
    results.append([
        gcp_name,
        x,
        y
    ])
    print(f"{gcp_name} -> ({x}, {y})")
    ax.plot(x, y, "r+", markersize=14)
    fig.canvas.draw_idle()
    next_gcp()


def onkey(event):
    # KEYBOARD EVENTS
    global mode
    global current_gcp
    # Mark mode
    if event.key == "m":
        if current_gcp < len(gcps):
            mode = "mark"
            print(
                f"\nCLICK ON IMAGE FOR {gcps[current_gcp]}"
            )
            update_title()
    # Not visible
    elif event.key == "0":
        if current_gcp < len(gcps):
            results.append([
                gcps[current_gcp],
                None,
                None
            ])
            print(
                f"{gcps[current_gcp]} -> NOT VISIBLE"
            )
            next_gcp()
    # Undo
    elif event.key == "u":
        if len(results) == 0:
            return
        removed = results.pop()
        current_gcp = max(0, current_gcp - 1)
        print(
            f"UNDO -> {removed}"
        )
        update_title()


dir = "1951_5129"

add_padding_prt_dir = r"D:\datasets\image_preprocessing\04_add_padding\penarth_head_to_cold_knap"
gcp_prt_dir = r"D:\datasets\image_preprocessing\03_gcps\penarth_head_to_cold_knap"

#  get the list of images in the directory
image_list = [f for f in os.listdir(os.path.join(add_padding_prt_dir, dir)) if f.endswith(".tif")]

gcp_file = os.path.join(gcp_prt_dir, dir, f"{dir}_gcp_cords.txt")


# -------------------------------- process gcp file

gcp_txt_df = pd.read_csv(gcp_file)
#  randomly split the GCP IDs into 2 groups in 80:20 ratio
n = len(gcp_txt_df)
labels = ["GCP_CoP"] * int(0.8 * n) + ["GCP_ChP"] * (n - int(0.8 * n))
random.seed(42)
random.shuffle(labels)
#  add a new column to the DataFrame with the combined label and GCP ID
gcp_txt_df["gcp_name"] = [f"{label}_{gcp_id}" for label, gcp_id in zip(labels, gcp_txt_df["ID"].tolist())]
#  get the list of GCP names
gcps = gcp_txt_df["gcp_name"].tolist()



# -------------------------------- process image file


# image_path = r"D:\datasets\image_preprocessing\04_add_padding\penarth_head_to_cold_knap\1951_5129\56_br_clahe_padded.tif"
result_list = []
for image_name in image_list:
    print(f"Processing image: {image_name}")
    image_path = os.path.join(add_padding_prt_dir, dir, image_name)
    # set variables
    results = []
    current_gcp = 0
    mode = "navigate"
    # load image
    img = Image.open(image_path)
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.imshow(img)
    title = ax.set_title(image_path)
    # connect events
    fig.canvas.mpl_connect("button_press_event", onclick)
    fig.canvas.mpl_connect("key_press_event", onkey)
    update_title()
    plt.show()
    #  remove any rows with None values (not visible) from the results
    results = [row for row in results if None not in row]
    result_list.append(results)


# create an empty DataFrame to store the results

#  empty df with columns for geo_x geo_y geo_z im_x im_y image_name [gcp_name]
gcp_out_txt_df = pd.DataFrame(columns=["geo_x", "geo_y", "geo_z", "im_x", "im_y", "image_name", "gcp_name"])

#  store the results in the gcp_out_txt_df
for results in result_list:
    for row in results:
        gcp_name, im_x, im_y = row
        gcp_row = gcp_txt_df[gcp_txt_df["gcp_name"] == gcp_name].iloc[0]
        geo_x = gcp_row["E(m)"]
        geo_y = gcp_row["N(m)"]
        geo_z = gcp_row["Elev(m)"]
        image_name = image_list[result_list.index(results)]
        gcp_out_txt_df.loc[len(gcp_out_txt_df)] = [geo_x, geo_y, geo_z, im_x, im_y, image_name, gcp_name]


# save the gcp_out_txt_df to a csv file
gcp_out_txt_df.to_csv(os.path.join(gcp_prt_dir, dir, f"{dir}_gcp_cords_ODM_all.csv"), index=False)


#  subset the gcp_out_txt_df to only include rows with GCP_CoP
gcp_out_txt_df_cop = gcp_out_txt_df[gcp_out_txt_df["gcp_name"].str.startswith("GCP_CoP")]
#  save the gcp_out_txt_df_cop to a txt file without header and index
gcp_out_txt_df_cop.to_csv(os.path.join(gcp_prt_dir, dir, f"{dir}_gcp_cords_ODM_CoP.txt"), index=False, header=False, sep=" ")
#  add a row to the output txt with EPSG string at the start of the file
with open(os.path.join(gcp_prt_dir, dir, f"{dir}_gcp_cords_ODM_CoP.txt"), "r") as f:
    lines = f.readlines()
    lines.insert(0, "EPSG:27700\n")

with open(os.path.join(gcp_prt_dir, dir, f"{dir}_gcp_cords_ODM_CoP.txt"), "w") as f:
    f.writelines(lines)


# subset the gcp_out_txt_df to only include rows with GCP_ChP
gcp_out_txt_df_chp = gcp_out_txt_df[gcp_out_txt_df["gcp_name"].str.startswith("GCP_ChP")]
#  save the gcp_out_txt_df_chp to a txt file without header and index
gcp_out_txt_df_chp.to_csv(os.path.join(gcp_prt_dir, dir, f"{dir}_gcp_cords_ODM_ChP.txt"), index=False, header=False, sep=" ")
# add a row to the output txt with EPSG string at the start of the file
with open(os.path.join(gcp_prt_dir, dir, f"{dir}_gcp_cords_ODM_ChP.txt"), "r") as f:
    lines = f.readlines()
    lines.insert(0, "EPSG:27700\n")

with open(os.path.join(gcp_prt_dir, dir, f"{dir}_gcp_cords_ODM_ChP.txt"), "w") as f:
    f.writelines(lines)



#  create geo.txt file to insert the EPSG code in first line and all image names in each lines
with open(os.path.join(gcp_prt_dir, dir, f"{dir}_geo.txt"), "w") as f:
    f.write("EPSG:27700\n")
    for image_name in image_list:
        f.write(f"{image_name}" + " geo_x geo_y geo_z" + " 0 0 0 200 50\n")

