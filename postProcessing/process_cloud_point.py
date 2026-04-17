# date: 13-04-2026
# author: MohantyB
# topic: cloud point post processing
# description: script to process the visualSfM cloud point data to
#              create point shapefile and subset the cloud point based
#              on Z values



from plyfile import PlyData, PlyElement
import numpy as np
import geopandas as gpd
from shapely.geometry import Point


x_constant = 312092.436
y_constant = 166719.0029
z_constant = 0.0
Z_threshold = 0.0
epsg_code = 27700 # British National Grid



def create_shapefile_from_ply(vertex_data: np.ndarray, out_shapefile_path: str,
                               epsg_code: int = 27700) -> None:
    '''
    function to create a shapefile from the ply cloud point data

    vertex_data: the vertex data from the ply file
    out_shapefile_path: the output path to save the shapefile
    epsg_code: the EPSG code for the CRS of the output shapefile,
               default is 27700 (British National Grid)

    Returns: None
    '''
    # get the x, y, z coordinates
    x = vertex_data['x']
    y = vertex_data['y']
    z = vertex_data['z']
    # creat a shapefile with the x and y coordinates and z as elevation
    # create a geodataframe
    print(f"Creating shapefile from ply data...")
    gdf = gpd.GeoDataFrame(geometry=[Point(xy) for xy in zip(x, y)],
                           data={'elevation': z})
    # add the coordinate reference system (CRS) to the geodataframe
    gdf.set_crs(epsg=epsg_code, inplace=True)
    print(f"Shapefile created with {len(gdf)} points.")
    # save the geodataframe as a shapefile
    print(f"Saving shapefile...")
    gdf.to_file(out_shapefile_path)
    print(f"Shapefile saved at: {out_shapefile_path}")

def resave_ply(vertex_data: np.ndarray, out_ply_path: str) -> None:
    '''
    function to resave the ply file with the modified vertex data

    vertex_data: the modified vertex data
    out_ply_path: the output path to save the modified ply file

    Returns: None
    '''
    # ensure vertex_data is a proper numpy structured array
    vertex_data = np.array(vertex_data)
    # create a new ply element with the modified vertex data
    vertex_element = PlyElement.describe(vertex_data, 'vertex')
    # save the new ply file
    PlyData([vertex_element], text=True).write(out_ply_path)
    print(f"Modified ply file saved at: {out_ply_path}")

#  input ply file path
in_ply_path = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_4.0.ply"
out_ply_path = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_4.0_modified.ply"
out_shapefile_path = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_4.0.shp"
out_subset_ply_path = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_4.0_subset.ply"
out_subset_shapefile_path = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_4.0_subset.shp"


# read the ply file
ply_data = PlyData.read(in_ply_path)
#  get the vertex data
vertex_data = ply_data['vertex']
# print(vertex_data.dtype)
print(f"Original ply data has {len(vertex_data)} points.")

# remap the x, y, z values to the original coordinates by adding the
# constants which was used in visualSFM GCP processing
vertex_data['x'] = vertex_data['x'] + x_constant
vertex_data['y'] = vertex_data['y'] + y_constant
vertex_data['z'] = vertex_data['z'] + z_constant

print('max z value after remapping:', np.max(vertex_data['z']))

# save the modified ply file
resave_ply(vertex_data, out_ply_path)

# create a shapefile from the ply data
create_shapefile_from_ply(vertex_data, out_shapefile_path, epsg_code)

# subset the ply cloud point based on Z values
vertex_data_subset = vertex_data[vertex_data['z'] > Z_threshold]

print(f"Subsetted ply data has {len(vertex_data_subset)} "
      f"points with Z > {Z_threshold}.")

# save the subset ply file
resave_ply(vertex_data_subset, out_subset_ply_path)

# create a shapefile from the subset ply data
create_shapefile_from_ply(vertex_data_subset, out_subset_shapefile_path,
                           epsg_code)

