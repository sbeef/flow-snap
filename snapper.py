import utm
import csv
import gdal
import numpy as np
import flowsnap as fs
import archook
archook.get_arcpy()
import arcpy

arcpy.env.overwriteOutput = True

RESUME = False

POINTS_CSV = 'alpts_utm.csv'
OUT_CSV = 'snapped_points.csv'
NAME_FIELD = 'Sample_nam'
ZONE_NUMBER = 47
BAND = 'R'
DATUM = 'WGS 1984'
MAX_DISTANCE = 5000
ACC_RASTER = 'srtm/srtm_acc.tif'
TEMP_DIR = 'clipped'
VERBOSE = True

DWEIGHT = 100
AWEIGHT = .000001

if BAND < 'N':
    hemisphere = 'S'
else:
    hemisphere = 'N'

coordinate_system = '%s UTM ZONE %d%s' % (DATUM, ZONE_NUMBER, hemisphere)

def do_reload():
    reload(fs)

def run(resume=RESUME, verbose=VERBOSE):
    with open(POINTS_CSV, 'r') as csvfile:
        results = []
        reader = csv.DictReader(csvfile)
        for row in reader:
            if verbose:
                print "on %s" % row[NAME_FIELD]
            x = float(row['utm47_x'])
            y = float(row['utm47_y'])
            #utms = utm.from_latlon(lat, lon)
            easting = x #utms[0]
            northing = y #utms[1]
            # area was reported in square Km, but we will be working with it as meters
            area = float(row['Catchmen_1'])*1000000
            # If max distance is set, we will clip the accumulation raser to a buffer around a point
            if MAX_DISTANCE is not None:
                min_x = easting-MAX_DISTANCE
                max_x = easting+MAX_DISTANCE
                min_y = northing-MAX_DISTANCE
                max_y = northing+MAX_DISTANCE
                rectangle = "%s %s %s %s" % (min_x, min_y, max_x, max_y)
                if verbose:
                    print "\t clipping"
                name = row[NAME_FIELD].replace('\*', 'star')
                outfile = "%s/point_%s_clip.tif" % (TEMP_DIR, name)
                if verbose:
                    print "clipping %s" % outfile
                if not arcpy.Exists(outfile) or not resume:
                    clipped_acc = arcpy.Clip_management(ACC_RASTER, rectangle, outfile)
                acc_to_use = outfile
                #acc_array = arcpy.RasterToNumPyArray("in_memory/clipped_acc")
            else:
                acc_to_use = ACC_RASTER
            if verbose:
                print "\t reading as array"
            ds = gdal.Open(acc_to_use)
            acc_array = np.array(ds.GetRasterBand(1).ReadAsArray())
            sample = (easting, northing)
            if verbose:
                print "\t snapping"
            result_row = fs.snap_pt_and_info(sample, area, ds, acc_array, DWEIGHT, AWEIGHT)
            result_row['Sample'] = row[NAME_FIELD]
            if verbose:
                print "\t %s snapped with %.4f distance offset, and %.4f area offset" % (result_row['Sample'], result_row['distance_offset'], result_row['area_offset'])
            results.append(result_row)
    with open(OUT_CSV, 'wb') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fs.get_field_names())
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
        
                
            
