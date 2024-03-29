import tempfile

import numpy as np
from osgeo import gdal

def check_rasters_alignment(raster_files):
    """
    Returns True only if all the raster files have the same alignment - projection, extent and resolution.
    Otherwise returns False.

    :param raster_files: a sequence of raster files.
    :rtype: float
    """

    # Take the last raster as the reference raster
    ref_raster = gdal.Open(raster_files[-1], gdal.GA_ReadOnly)
    ref_proj = ref_raster.GetProjection()
    ref_transform = ref_raster.GetGeoTransform()
    ref_size = (ref_raster.RasterXSize, ref_raster.RasterYSize)

    for rfile in raster_files[:-1]:
        raster = gdal.Open(rfile, gdal.GA_ReadOnly)
        if not raster.GetProjection() == ref_proj:
            return False

        if not (raster.RasterXSize, raster.RasterYSize) == ref_size:
            return False

        if not raster.GetGeoTransform() == ref_transform:
            return False

    return True


def open_and_reproject_raster(rast_file, ref_rast_file, feedback=None):
    """
    Opens and optionally reprojects a raster to the reference's raster projection,
    extent and resolution.

    :param rast_file: the raster file to be opened and optionally reprojected.
    :param ref_rast_file: the reference raster.
    :param feedback: (optional) a QgsProcessingFeedback instance.
    """
    ref_raster = gdal.Open(ref_rast_file, gdal.GA_ReadOnly)
    ref_proj = ref_raster.GetProjection()
    ref_transform = (xmin, xres, xskew, ymax, yskew, yres) = ref_raster.GetGeoTransform()
    ref_size = (ref_raster.RasterXSize, ref_raster.RasterYSize)

    raster = gdal.Open(rast_file, gdal.GA_ReadOnly)

    kwargs = {}
    if raster.GetProjection() != ref_proj:
        kwargs['dstSRS'] = ref_proj
    if (raster.RasterXSize, raster.RasterYSize) != ref_size:
        kwargs['width'] = ref_size[0]
        kwargs['height'] = ref_size[1]
    if raster.GetGeoTransform() != ref_transform:
        xmax = xmin + (xres * ref_size[0])
        ymin = ymax + (yres * ref_size[1])
        kwargs['outputBounds'] = (xmin, ymin, xmax, ymax)

    if kwargs:
        if feedback:
            feedback.pushInfo(f"\nReprojecting and warping '{rast_file}' to the "
                              f"reference's raster extent, cellsize, and CRS...")
        warp_options = gdal.WarpOptions(resampleAlg=gdal.GRA_NearestNeighbour, **kwargs)
        dest_file = tempfile.NamedTemporaryFile(delete=False)
        raster = gdal.Warp(dest_file.name, raster, options=warp_options)

    return raster