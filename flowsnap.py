import numpy as np
import math, gdal

# These functions are for caclulating the optimal location on a given flow accumulation (upstream area
# raster) of a reported point with associated upstream area.

def get_min_entry(array):
    """Returns the row/column location of the minimum point"""
    minimum = np.argmin(array)
    rows, columns = np.shape(array)
    return np.array([(minimum/columns), (minimum%columns)])

def array_entry_to_location(entry, origin, res):
    """gives the geographic location of an array entry.  Works in either row/column or x/y format.

    Keyword Arguments:
    entry -- the aray entry
    origin -- the geographic location of the raster origin point
    res -- the size of the cell in geographic units of the raster
    """
    return origin+(entry*res)

def get_distance_grid(rows, columns, entry):
    """creates an array representing distance from a point in row/column format

    Keyword Arguments:
    rows -- the number of rows in the distance grid
    columns -- the number of columns in the distance grid
    entry -- the entry in the array to get distance from (in row/column format\
    """
    X,Y = np.meshgrid(np.arange(columns), np.arange(rows))
    return ((Y-entry[0])**2 + (X-entry[1])**2)**(0.5)

def location_to_array_entry(location, origin, res):
    """gives the entry in an array of a geographic location.  Works in either row/column or x/y format.

    Keyword Arguments:
    location -- the geographic location to find array coordinates of
    origin -- the geographic location of the raster origin.
    res -- the size of the cell in geographic units of the raster
    """
    return np.rint((np.absolute(location-origin))/res)

def upstream_to_pixels(upstream_area, cellsize):
    """Gives an upstream area in number of pixels"""
    return upstream_area/(cellsize**2)

def get_area_matrix(upstream_area, acc_array, geotransform):
    """gets a matrix representing difference of upstream area from a given value

    Keyword Arguments:
    upstream_area -- the upstream area to calculate difference from, in raster units
    acc_array -- an array representing the upstream area of each point.
    geotransform -- the geotransform of the accumulation raster
    """
    upstream_pixels = upstream_to_pixels(upstream_area, geotransform[1])
    return np.absolute((acc_array-upstream_pixels))

def get_rating_grid(sample, dweight, aweight, upstream_area, acc_array, geotransform, dataset):
    """Gets a matrix representing how best each cell matches a given point and upstream area.

    Keyword Arguments:
    sample -- the location of the point of interest in geographic coordiantes (x/y format)
    dweight -- the ammount to weight distance from point by
    aweight -- the ammount to weight difference in area by
    upstream_area -- the upstream area of the point in question, in raster units
    acc_array -- numpy array representing upstream area of each point.
    geotransform -- the geotransform of the numpy array
    dataset -- the GDAL dataset of the accumulation raster
    """
    Xsize = dataset.RasterXSize
    Ysize = dataset.RasterYSize
    resolution = geotransform[1]
    # now we switch to row column instead of x, y
    origin = np.array([geotransform[3], geotransform[0]])
    rc_sample = np.array([sample[1], sample[0]])
    sample_location = location_to_array_entry(rc_sample, origin, resolution)
    distance_grid = get_distance_grid(Ysize, Xsize, sample_location)
    area_grid = get_area_matrix(upstream_area, acc_array, geotransform)
    rating_grid = (distance_grid*(1/dweight))+(area_grid*(1/aweight))
    return rating_grid

def reported_pt_to_raster_pt(sample, upstream_area, acc_array, dataset, dweight=1, aweight=1):
    """gets the best matching point (and assoicated area) on a raster for a reported point and
       upstream area.

    Keyword Arguments:
    sample -- the location of a point of interest in geographic coordiante (x/y format)
    upstream_area -- the upstream area of the point in question, in raster units
    acc_array -- the numpy array representing the upstream area of each point.
    dataset -- the GDAL dataset of the accumulation raster
    dweight -- the ammount to weight distance from point by (default 1)
    aweight -- the ammount to weight difference in area by (default 1)
    """
    gtf = dataset.GetGeoTransform()
    rg = get_rating_grid(sample, dweight, aweight, upstream_area, acc_array, gtf, dataset)
    best = get_min_entry(rg)
    best_loc = array_entry_to_location(best, np.array([gtf[3], gtf[0]]), gtf[1])
    area = acc_array[best[0]][best[1]]
    return (np.array([best_loc[1], best_loc[0]]), area)
    
def snap_pt_and_info(sample, upstream_area, dataset, acc_array, dweight=1, aweight=1):
    """gets the best matching point (and assoicated area) on a raster for a reported point and
       upstream area.

    Keyword Arguments:
    sample -- the location of a point of interest in geographic coordiante (x/y format)
    upstream_area -- the upstream area of the point in question, in raster units
    dataset -- the GDAL dataset of the accumulation raster
    dweight -- the ammount to weight distance from point by (default 1)
    aweight -- the ammount to weight difference in area by (default 1)
    """
    gtf = dataset.GeGeoTransform()
    snaped, area = reported_pt_to_raster_pt(sample, upstream_area, acc_array, dataset, dweight, aweight)
    origin = np.array([gtf[0], gtf[3]])
    distance = numpy.linalg.norm(snaped-origin)
    snaped_area = area*(gtf[1]**2)
    size_dif = abs(upstream_area-snaped_area)
    return {'reported_x' = sample[0],
            'reported_y' = sample[1],
            'reported_area' = upstream_area,
            'snaped_x' = snaped[0],
            'snaped_y' = snaped[1],
            'snaped_area' = snaped_area,
            'distance_offset' = distance,
            'area_offset' = size_dif}
            
