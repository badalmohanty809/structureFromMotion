
import pdal
import json

# define the input cloud file path
in_cloud_file_path = r"D:\OpenDroneMap\1951_5129\odm_georeferenced_model_cc.laz"
# define the output cloud file path
out_cloud_file_path = r"D:\OpenDroneMap\1951_5129\odm_georeferenced_model_cc_filtered.laz"
out_dtm_file_path = r"D:\OpenDroneMap\1951_5129\odm_georeferenced_model_cc_filtered.tif"


pipeline_json = {
    "pipeline": [
        in_cloud_file_path,
        {
            "type": "filters.outlier",
            "method": "statistical",
            "mean_k": 16,
            "multiplier": 2.0
        },
        {
            "type": "filters.smrf",
            "window": 24,
            "slope": 0.5,
            "threshold": 0.7,
            "scalar": 1.5
        },
        {
            "type": "filters.hag_delaunay"
        },
        {
            "type": "filters.range",
            "limits": "HeightAboveGround[0:0.5]"
        },
        out_cloud_file_path
    ]
}

pipeline = pdal.Pipeline(json.dumps(pipeline_json))

num_points = pipeline.execute()

print(f"Ground points retained: {num_points}")



pipeline_json = {
    "pipeline": [
        out_cloud_file_path,
        {
            "type": "writers.gdal",
            "filename": out_dtm_file_path,
            "resolution": 0.25,
            "output_type": "min",
            "gdaldriver": "GTiff"
        }
    ]
}

pipeline = pdal.Pipeline(json.dumps(pipeline_json))
pipeline.execute()

print(f"DTM saved as {out_dtm_file_path}")