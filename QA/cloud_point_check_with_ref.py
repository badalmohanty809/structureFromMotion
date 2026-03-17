# date: 17-03-2026
# author: MohantyB
# topic: cloud point QA
# description: script to check the cloud point data with reference data

import os
import sys
import pandas as pd
from osgeo import gdal
import numpy as np
import matplotlib.pyplot as plt
sys.path.append("C:\\Users\\c25045127\\OneDrive - Cardiff University\\data_analysis\\structureFromMotion\\utils\\")
import common_python_functions as cpf




in_cloud_point_path = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_1.0_georeferenced_try_1.txt"
ref_tif_path = "C:\\Users\\c25045127\\OneDrive - Cardiff University\\datasets\\WCMC\\"
out_path = "D:\\datasets\\QA\\1944_4001\\"

#  read the cloud point data
cloud_point_df = pd.read_csv(in_cloud_point_path, sep=",")
#  remove rows if any of the X, Y, Z values are missing
cloud_point_df = cloud_point_df.dropna(subset=["//X", "Y", "Z"])

# read the reference data
ref_tif_files = [f for f in os.listdir(ref_tif_path) if f.endswith(".tif")]

# merge the ref tif files into a single tif file with gdal builtvrt
ref_vrt_merged_path = os.path.join(out_path, "merged_ref.vrt")
gdal.BuildVRT(ref_vrt_merged_path, [os.path.join(ref_tif_path, f) for f in ref_tif_files])

# open the merged ref raster
ref_ds = gdal.Open(ref_vrt_merged_path, gdal.GA_ReadOnly)
ref_band = ref_ds.GetRasterBand(1)

#  get the raster metadata and open the merged ref raster
meta = cpf.get_raster_metadata(ref_vrt_merged_path)

ref_elev = []
# loop through the cloud points and get the corresponding value from the
#  merged ref raster
for idx, row in cloud_point_df.iterrows():
    lat = row["Y"]
    lon = row["//X"]
    rowcol = cpf.latlon_to_rowcol(
        lat,
        lon,
        geotransform=meta["geotransform"],
        width=meta["width"],
        height=meta["height"],
        raster_crs=meta.get("raster_crs"),
        input_crs=meta.get("raster_crs"),
        return_float=False,
    )
    if rowcol is not None:
        r, c = rowcol
        ref_value = ref_band.ReadAsArray(c, r, 1, 1)[0, 0]
        if ref_value == ref_band.GetNoDataValue():
            ref_value = None
        ref_elev.append(ref_value)
        print(f"Cloud point {idx}: lat={lat}, lon={lon} -> raster value={ref_value}")
    else:
        ref_elev.append(None)
        print(f"Cloud point {idx}: lat={lat}, lon={lon} is outside raster bounds.")


cloud_point_df_out = cloud_point_df.copy()
cloud_point_df_out["ref_z"] = ref_elev
#  drop rows where ref_z is None
cloud_point_df_out = cloud_point_df_out.dropna(subset=["ref_z"])
# add a new column to the output dataframe which is the difference between ref_z and Z
cloud_point_df_out["ref_sfm_diff"] = cloud_point_df_out["ref_z"] - cloud_point_df_out["Z"]
# save the output dataframe to a txt file
cloud_point_df_out.to_csv(os.path.join(out_path, "1944_4001_vsfm_try_1.0_georeferenced_try_1_ref_z.txt"), index=False)


#  plot the data

#  get the sfm z values from the cloud point data
sfm_z = cloud_point_df_out["Z"].values
ref_z = cloud_point_df_out["ref_z"].values

#  plot the ref_z in x axis and sfm_z in y axis
plt.figure(figsize=(8, 6))
plt.scatter(ref_z, sfm_z, marker='.', linewidths=0)
plt.xlabel("Reference Z")
plt.ylabel("SfM Z")
plt.title("SfM Z vs Reference Z")
z = np.polyfit(ref_z, sfm_z, 1)  # linear regression
p = np.poly1d(z)
x_trend = np.array([z_min, z_max])
plt.plot(x_trend, p(x_trend), color='red', linestyle='--', label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
plt.grid()
plt.legend()
# save the plot
plt.savefig(os.path.join(out_path, "sfm_z_vs_ref_z.png"))
plt.show()


#  subset the cloud point data to only include points where the Z value is greater than a threshold (e.g., 10)
threshold = 0
cloud_point_df_out_subset = cloud_point_df_out[cloud_point_df_out["Z"] > threshold]

#  plot the ref_z in x axis and sfm_z in y axis for the subsetted data
plt.figure(figsize=(8, 6))
plt.scatter(cloud_point_df_out_subset["ref_z"], cloud_point_df_out_subset["Z"], marker='.', linewidths=0)
plt.xlabel("Reference Z")
plt.ylabel("SfM Z")
plt.title(f"SfM Z vs Reference Z (SfMZ > {threshold})")
z_subset = np.polyfit(cloud_point_df_out_subset["ref_z"], cloud_point_df_out_subset["Z"], 1)  # linear regression
p_subset = np.poly1d(z_subset)
x_trend_subset = np.array([cloud_point_df_out_subset["ref_z"].min(), cloud_point_df_out_subset["ref_z"].max()])
plt.plot(x_trend_subset, p_subset(x_trend_subset), color='red', linestyle='--', label=f'Trend: y={z_subset[0]:.2f}x+{z_subset[1]:.2f}')
plt.grid()
plt.legend()
plt.savefig(os.path.join(out_path, "sfm_z_vs_ref_z_subset.png"))
plt.show()
