# date: 14-04-2026
# author: MohantyB
# topic: cloud point post processing
# description:



import open3d as o3d
import numpy as np
from plyfile import PlyData, PlyElement
import CSF
from scipy.spatial import cKDTree

from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator
import rasterio
from rasterio.transform import from_origin




in_ply_path = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_4.0_modified.ply"
out_cleaned_ply_path = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_4.0_cleaned.ply"
out_cleaned_ground_ply_path = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_4.0_cleaned_ground.ply"
out_cleaned_nonground_ply_path = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_4.0_cleaned_nonground.ply"
out_cleaned_only_ground_ply_path = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_4.0_cleaned_only_ground.ply"
out_tif = "D:\\datasets\\sfm_outputs\\gcps\\1944_4001\\1944_4001_vsfm_try_4.0_dtm.tif"

# Load the PLY file
pcd = o3d.io.read_point_cloud(in_ply_path)
print("Original point count:", np.asarray(pcd.points).shape[0])

def read_ply_with_plyfile(ply_path: str) -> np.ndarray:
    '''
    function to read a ply file using plyfile and return the point cloud
    as a numpy array

    ply_path: path to the input ply file

    return: point cloud as numpy array of shape (N, 3)
    '''
    plydata = PlyData.read(ply_path)
    vertex = plydata['vertex'].data
    points = np.vstack((vertex['x'], vertex['y'], vertex['z'])).T
    print(f"Read {points.shape[0]} points from {ply_path}")
    return points


def remove_outliers(pcd: o3d.geometry.PointCloud, nb_neighbors: int = 20,
                    std_ratio: float = 2.0, nb_points: int = 8,
                    radius: float = 100) -> o3d.geometry.PointCloud:
    '''
    function to remove outliers from the point cloud using statistical
    outlier removal and radius outlier removal

    pcd: input point cloud as open3d PointCloud object
    nb_neighbors: specifies how many neighbors are taken into account in
                  order to calculate the average distance for a given
                  point
    std_ratio: allows setting the threshold level based on the standard
               deviation of the average distances across the point cloud
               Lower number do more aggressive filtering
    nb_points: lets you pick the minimum amount of points that the
               sphere should contain
    radius (m): defines the radius of the sphere that will be used for
            counting the neighbors

    return: cleaned point cloud as open3d PointCloud object
    '''
    print("Starting outlier removal of point cloud...")
    # Remove NaN / infinite values (safety)
    print("\tRemoving non-finite points...")
    pcd.remove_non_finite_points()
    if len(pcd.points) == 0:
        print("\t\tNo valid points after removing non-finite points.")
        return pcd
    print("\t\tAfter removing non-finite points:", len(pcd.points))
    # Statistical Outlier Removal
    # statistical_outlier_removal removes points that are further away from
    # their neighbors compared to the average for the point cloud.
    print("\tRemoving statistical outliers...")
    pcd_stat, _ = pcd.remove_statistical_outlier(
        nb_neighbors=nb_neighbors,
        std_ratio=std_ratio
    )
    if len(pcd_stat.points) == 0:
        print("\t\tNo valid points after statistical outlier removal.")
        return pcd_stat
    print("\t\tAfter statistical outlier removal:", len(pcd_stat.points))
    # Radius Outlier Removal
    # radius_outlier_removal removes points that have few neighbors in a
    # given sphere around them.
    print("\tRemoving radius outliers...")
    pcd_clean, _ = pcd_stat.remove_radius_outlier(
        nb_points=nb_points,
        radius=radius
    )
    if len(pcd_clean.points) == 0:
        print("\t\tNo valid points after radius outlier removal.")
        return pcd_clean
    print("\t\tAfter radius outlier removal:", len(pcd_clean.points))
    return pcd_clean


def create_ply_from_points(points: np.ndarray) -> PlyElement:
    '''
    function to create a ply element from a numpy array of points

    points: input point cloud as numpy array of shape (N, 3)

    return: ply element containing the point cloud data
    '''
    # create a structured array for the vertex data
    vertex = np.empty(
        points.shape[0],
        dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4')]
    )
    vertex['x'] = points[:, 0]
    vertex['y'] = points[:, 1]
    vertex['z'] = points[:, 2]
    element = PlyElement.describe(vertex, 'vertex')
    print(f"\tPly element created with {len(vertex)} vertices.")
    return element

def filter_with_csf(points: np.ndarray, csf_param: dict) -> tuple:
    '''
    function to filter the point cloud into ground and non-ground points
    using Cloth Simulation Filtering (CSF)
    CSF is a method for classifying ground and non-ground points in a
    point cloud. It simulates a cloth being draped over the point cloud
    and identifies ground points based on how the cloth interacts with
    the terrain.

    points: input point cloud as numpy array of shape (N, 3)
    csf_param: dictionary containing CSF parameters

    return: tuple containing indices of ground and non-ground points
    '''
    # Initialize CSF object
    print("Initializing CSF ground classification...")
    csf = CSF.CSF()
    # Assign point cloud
    print("\tAssigning point cloud to CSF...")
    csf.setPointCloud(points)
    # CSF parameters initialization
    print("\tSetting CSF parameters...")
    # Smooth steep terrain
    csf.params.bSloopSmooth = csf_param.get('bSloopSmooth', True)
    # Cloth resolution (m) - smaller = more detailed, but slower
    # Cloth resolution refers to the grid size (the unit is same as the
    # unit of pointclouds) of cloth which is used to cover the terrain.
    # The bigger cloth resolution you have set, the coarser DTM
    # you will get
    csf.params.cloth_resolution = csf_param.get('cloth_resolution', 0.7)
    # Higher = urban / flatter terrain - 1=flexible, 3=default, 5=rigid
    csf.params.rigidness = csf_param.get('rigidness', 1)
    csf.params.time_step = csf_param.get('time_step', 0.65)
    # Tighter = stricter ground, distance threshold (m)
    # Classification threshold refers to a threshold (the unit is same
    # as the unit of pointclouds) to classify the pointclouds into
    # ground and non-ground parts based on the distances between points
    # and the simulated terrain
    csf.params.class_threshold = csf_param.get('class_threshold', 7)
    # How long cloth settles (iterations)
    # Max iterations refers to the maximum iteration times of terrain
    # simulation
    csf.params.iterations = csf_param.get('iterations', 300)
    # Run CSF filtering
    # a list to indicate the index of ground points after calculation
    ground_idx = CSF.VecInt()
    # a list to indicate the index of non-ground points after calculation
    nonground_idx = CSF.VecInt()
    print("\tRunning CSF ground classification...")
    csf.do_filtering(ground_idx, nonground_idx)
    print("\tCSF ground classification completed.")
    # convert the ground and non-ground indices to numpy arrays
    ground_idx = np.array(ground_idx)
    nonground_idx = np.array(nonground_idx)
    print("\tGround points:", ground_idx.shape[0])
    print("\tNon-ground points:", nonground_idx.shape[0])
    return ground_idx, nonground_idx


def remove_residual_outliers(ground_points: np.ndarray, radius: float = 10.0,
                           z_threshold: float = 3.0) -> np.ndarray:
    '''
    function to remove residual outliers from the ground point cloud
    based on local Z consistency
    This removes points that deviate significantly in elevation
    from their local neighborhood, which can help clean up remaining
    outliers in the ground classification. The parameters can be
    adjusted based on the expected terrain variability and point cloud
    density initialize a spatial index for efficient neighbor queries

    ground_points: input ground point cloud as numpy array of
                   shape (N, 3)
    radius: radius (in meters) to search for neighboring points
    z_threshold: Z deviation threshold (in meters) to identify outliers

    return: filtered ground point cloud as numpy array of shape (M, 3)
    '''
    # Residual ground outlier removal (local Z consistency)
    print("Removing residual outliers from ground points...")
    tree = cKDTree(ground_points[:, :2])
    # mask to keep track of valid ground points
    print("\tInitial ground point count:", ground_points.shape[0])
    mask = np.ones(ground_points.shape[0], dtype=bool)
    # for each ground point, find neighbors within radius and
    # check Z consistency
    print("\tChecking local Z consistency for each ground point...")
    for i, p in enumerate(ground_points):
        idx = tree.query_ball_point(p[:2], radius)
        if len(idx) < 5:
            mask[i] = False
            continue
        # compare point's Z with median Z of neighbors
        local_z = ground_points[idx, 2]
        median_z = np.median(local_z)
        # if point's Z deviates from median by more than threshold,
        # mark as outlier
        if abs(p[2] - median_z) > z_threshold:
            mask[i] = False
    # apply mask to keep only valid ground points
    ground_points_masked = ground_points[mask]
    print("\tAfter residual outliers removed:", ground_points_masked.shape[0])
    return ground_points_masked


# STEP 0: load the VisualSFM output and translate it without doing thersholding

#  WRITE IT FROM THE PROCESS_CLOUD_POINT.PY FILE

# STEP 1: Point cloud outlier removal
print("Removing outliers from point cloud...")
pcd_clean = remove_outliers(pcd, nb_neighbors=20, std_ratio=2.0, nb_points=8,
                            radius=100)
print("Outlier removal completed")
# Save cleaned point cloud
o3d.io.write_point_cloud(out_cleaned_ply_path, pcd_clean)
print("Cleaned point cloud saved to:", out_cleaned_ply_path)

# STEP 2: Ground Classification

# reload the cleaned point cloud
points = read_ply_with_plyfile(out_cleaned_ply_path)
print("Input point count:", points.shape[0])
# Filter with CSF and save ground and non-ground points
csf_param = {
    'bSloopSmooth': True,
    'cloth_resolution': 0.7,
    'rigidness': 1,
    'time_step': 0.65,
    'class_threshold': 7,
    'iterations': 300
}
# get the indices of ground and non-ground points using CSF
print("Starting CSF ground classification...")
ground_idx, nonground_idx = filter_with_csf(points, csf_param)
print("CSF ground classification completed")
# create separate point clouds for ground and non-ground points
print("Creating point clouds for ground ...")
ground_element = create_ply_from_points(points[ground_idx])
PlyData([ground_element], text=False).write(out_cleaned_ground_ply_path)
print("Ground-only point cloud written: " + out_cleaned_ground_ply_path)
print("Non-ground points:", nonground_idx.shape[0])
print("Creating point clouds for non-ground ...")
nonground_element = create_ply_from_points(points[nonground_idx])
PlyData([nonground_element], text=False).write(out_cleaned_nonground_ply_path)
print("Non-ground points written: " + out_cleaned_nonground_ply_path)


# STEP 3: Ground‑Only Surface Refinement

# reload the ground-only point cloud
ground_points = read_ply_with_plyfile(out_cleaned_ground_ply_path)
print("Ground-only point count:", ground_points.shape[0])

# remove residual outliers from ground points
ground_points_refined = remove_residual_outliers(ground_points, radius=10.0,
                                                  z_threshold=3.0)



#  skiping other steps of step 3 for now

# save the refined ground point cloud
refined_ground_element = create_ply_from_points(ground_points_refined)
PlyData([refined_ground_element], text=False).write(out_cleaned_only_ground_ply_path)
print("Refined ground point cloud saved to: " + out_cleaned_only_ground_ply_path)


# STEP 4: Rasterization and DTM Generation

# reload the ground-only point cloud
ground_points = read_ply_with_plyfile(out_cleaned_ground_ply_path)
print("Ground-only point count:", ground_points.shape[0])


x = ground_points[:, 0]
y = ground_points[:, 1]
z = ground_points[:, 2]

cell_size = 1  # meters

# compute raster bounds
xmin, xmax = x.min(), x.max()
ymin, ymax = y.min(), y.max()

ncols = int((xmax - xmin) / cell_size) + 1
nrows = int((ymax - ymin) / cell_size) + 1

print("Raster size:", nrows, "rows x", ncols, "cols")

# create interpolation grid
xi = np.linspace(xmin, xmax, ncols)
yi = np.linspace(ymax, ymin, nrows)  # top-to-bottom
Xi, Yi = np.meshgrid(xi, yi)

# build TIN and interpolate

print("Building Delaunay triangulation...")
tri = Delaunay(ground_points[:, :2])

print("Interpolating terrain...")
interp = LinearNDInterpolator(tri, z)
Zi = interp(Xi, Yi)

nodata = -9999

Zi_filled = np.where(np.isnan(Zi), nodata, Zi)

transform = from_origin(
    xmin,
    ymax,
    cell_size,
    cell_size
)

with rasterio.open(
    out_tif,
    "w",
    driver="GTiff",
    height=Zi_filled.shape[0],
    width=Zi_filled.shape[1],
    count=1,
    dtype="float32",
    crs=None,        # set explicitly if known (EPSG:xxxx)
    transform=transform,
    nodata=nodata
) as dst:
    dst.write(Zi_filled.astype("float32"), 1)

print("DTM written:", out_tif)


