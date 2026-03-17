# date: 17-03-2026
# author: MohantyB
# topic: common python functions
# description: script to contain common python functions that can be
#              used across different scripts in the project


from osgeo import gdal
from math import floor
from typing import Optional, Tuple


def get_raster_metadata(raster_path: str) -> dict:
    '''
    function to get raster metadata including geotransform and CRS from a raster file using GDAL.

    Parameters
    ----------
    raster_path : str
        Path to the raster file.
    Returns
    -------
    dict
        A dictionary containing raster metadata:
        - width: raster width in pixels
        - height: raster height in pixels
        - geotransform: GDAL geotransform tuple (x0, a, b, y0, d, e)
        - raster_crs_wkt: CRS in WKT format
        - raster_crs: Optional CRS as string (e.g., "EPSG:27700") if available
    '''
    # Open the raster dataset
    ds = gdal.Open(raster_path, gdal.GA_ReadOnly)
    if ds is None:
        raise FileNotFoundError(f"Cannot open raster: {raster_path}")
    # Get geotransform and projection
    gt = ds.GetGeoTransform()  # (x0, a, b, y0, d, e)
    metadata = {
        "width": ds.RasterXSize,
        "height": ds.RasterYSize,
        "geotransform": gt,
        "raster_crs_wkt": ds.GetProjection(),  # WKT string
    }
    # Optional: try getting EPSG code as string like "EPSG:27700"
    proj = ds.GetSpatialRef()
    if proj is not None:
        auth_name = proj.GetAuthorityName(None)
        auth_code = proj.GetAuthorityCode(None)
        if auth_name and auth_code:
            metadata["raster_crs"] = f"{auth_name}:{auth_code}"
    # Clean up
    ds = None
    return metadata

def latlon_to_rowcol(
    lat: float,
    lon: float,
    geotransform: Tuple[float, float, float, float, float, float],
    width: int,
    height: int,
    raster_crs: Optional[str] = None,
    input_crs: str = "EPSG:4326",
    return_float: bool = False,
):
    """
    Convert a lat/lon to raster row/col using metadata only.

    Parameters
    ----------
    lat, lon : float
        Input coordinates (usually in EPSG:4326 unless input_crs is set differently).
    geotransform : tuple[6]
        GDAL geotransform: (x0, a, b, y0, d, e)
        Xgeo = x0 + a*col + b*row
        Ygeo = y0 + d*col + e*row
    width, height : int
        Raster dimensions in pixels.
    raster_crs : str | None
        CRS of raster (e.g., "EPSG:27700"). If provided and different from input_crs,
        coordinates are transformed with pyproj.
    input_crs : str
        CRS of input coordinates.
    return_float : bool
        If True, return fractional (row, col). Else return integer pixel index.

    Returns
    -------
    (row, col) or None
        None if point is outside raster bounds.
    """
    x, y = lon, lat
    # Reproject from input CRS to raster CRS if needed
    if raster_crs and input_crs and raster_crs != input_crs:
        try:
            from pyproj import Transformer
        except ImportError as exc:
            raise ImportError(
                "pyproj is required for CRS transformation. " \
                "Install with: pip install pyproj"
            ) from exc
    # transform coordinates to raster CRS
        transformer = Transformer.from_crs(input_crs, raster_crs,
                                           always_xy=True)
        x, y = transformer.transform(lon, lat)
    # apply inverse geotransform to get fractional row/col
    x0, a, b, y0, d, e = geotransform
    # Invert the 2x2 affine part:
    # [x - x0] = [a b] [col]
    # [y - y0]   [d e] [row]
    det = a * e - b * d
    if det == 0:
        raise ValueError("Invalid geotransform: " \
                            "non-invertible affine matrix (det=0).")
    # Calculate fractional column and row
    col_f = ( e * (x - x0) - b * (y - y0)) / det
    row_f = (-d * (x - x0) + a * (y - y0)) / det
    # If return_float is True, return the fractional row and column
    if return_float:
        return row_f, col_f
    # Otherwise,
    # convert to integer pixel index (upper-left inclusive convention)
    # Convert to pixel index (upper-left inclusive convention)
    row = floor(row_f)
    col = floor(col_f)
    # Check if the resulting row and column are within the raster bounds
    # Bounds check
    if row < 0 or row >= height or col < 0 or col >= width:
        return None
    # If within bounds, return the row and column as integers
    return row, col

