
import pdal
import json
import subprocess


project = "1944_4001"

# define the input cloud file path
in_cloud_file_path = r"D:\OpenDroneMap\\" + project + r"\odm_georeferenced_model_cc.laz"
# define the output cloud file path
out_cloud_file_path = r"D:\OpenDroneMap\\" + project + r"\odm_georeferenced_model_cc_filtered_5.laz"
out_dtm_file_path = r"D:\OpenDroneMap\\" + project + r"\odm_georeferenced_model_cc_filtered_5.tif"
out_filled_dtm_file_path = r"D:\OpenDroneMap\\" + project + r"\odm_georeferenced_model_cc_filtered_filled_5.tif"


pipeline_json = {
    "pipeline": [
        in_cloud_file_path,
        {
            "type": "filters.outlier",
            "method": "statistical",
            "mean_k": 24,
            "multiplier": 1.5
        },
        {
            "type": "filters.outlier",
            "method": "radius",
            "radius": 0.5,
            "min_k": 8
        },
        {
            "type":"filters.range",
            "limits":"Classification![7:7]"
        },
        {
            "type": "filters.smrf",
            "window": 8,
            "slope": 1.2,
            "threshold": 1.0,
            "scalar": 1.25
        },
        {
            "type": "filters.range",
            "limits": "Classification[2:2]"
        },
{
            "type": "filters.reprojection",
            "out_srs": "EPSG:27700"
        },
        out_cloud_file_path
    ]
}

pipeline = pdal.Pipeline(json.dumps(pipeline_json))
num_points = pipeline.execute()

print(f"Ground points retained: {num_points}")


# ----------------------- generate the DTM from the filtered point cloud using IDW interpolation

pipeline_json = {
    "pipeline": [
        out_cloud_file_path,
        {
            "type": "writers.gdal",
            "filename": out_dtm_file_path,
            "resolution": 0.5,
            "radius": 1.5,
            "output_type": "idw",
            "gdaldriver": "GTiff",
            "data_type": "float32",
            "nodata": -9999,
            "gdalopts": "COMPRESS=DEFLATE,TILED=YES"
        }
    ]
}

pipeline = pdal.Pipeline(json.dumps(pipeline_json))
pipeline.execute()

print(f"DTM saved as {out_dtm_file_path}")


# ----------------------- fill the DTM using GDAL FillNodata

gdal_fill_nodata_command = f'gdal_fillnodata -md 5 -of GTiff -co "COMPRESS=DEFLATE" -co "TILED=YES" "{out_dtm_file_path}" "{out_filled_dtm_file_path}"'

subprocess.run(gdal_fill_nodata_command, shell=True, check=True)

print(f"Filled DTM saved as {out_filled_dtm_file_path}")
