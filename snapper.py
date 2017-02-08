import utm
import csv
import gdal

POINTS_CSV = ''
ZONE_NUMBER = 47
BAND = 'R'
DATUM = 'WGS 1984
MAX_DISTANCE = 

if BAND < 'N':
    hemisphere = 'S'
else:
    hemisphere = 'N'

coordinate_system = '%s UTM ZONE %d%s' % (DATUM, ZONE_NUMBER, hemisphere)

with open(POINTS_CSV) as csvfile:
    reader = csv.DictReader(csvfile):
        for row in reader:
            easting, northing = utm.from_latlon(row['lat'], row['long'])
            # area was reported in square Km, but we will be working with it as meters
            area = row['area']*1000000
            # If max distance is set, we will clip the accumulation raser to a buffer around a point
            if MAX_DISTANCE is not None:
                min_x = easting-MAX_DISTANCE
                max_x = easting+MAX_DISTANCE
                min_y = northing-MAX_DISTANCE
                max_y = northing+MAX_DISTANCE
                rectangle = "%s %s %s %s" % (min_x, min_y, max_x, max_y)  
                clipped_acc = arcpy.Clip_management(ACC_RASTER, rectangle, "in_memory/clipped_acc")
                acc_array = arcpy.RasterToNumPyArray(clipped_acc)
            else:
                ds = gdal.Open(ACC_RASTER)
                acc_array = np.array(ds.GetRasterBand(1).ReadAsArray())
            sample = (easting, northing)
            result_row = fs.snap_pt_and_info(sample, row['area'], ds, acc_array, DWEIGHT, AWEIGHT)
            results.append(results_row)
                
            
