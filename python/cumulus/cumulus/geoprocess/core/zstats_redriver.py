import argparse
from datetime import datetime, timedelta
import json
import logging
import os
from rasterstats import zonal_stats
import subprocess
import tempfile
from timeit import default_timer as timer
from uuid import uuid4


# THIS SCRIPT IS DEVELOPED AS A QUICK ONE-OFF
# IT SHOULD BE GENERALIZED IN THE FUTURE WHEN POSSIBLE
# BEWARE OF HARD-CODING LIKE "/var/www/html"

def warp_to_vrt(infile, outfile, extra_args=None):
    """
    Convert SNODAS file to geotiff format
    """

    logging.info('  gdalwarp; infile: {}; outfile: {}'.format(infile, outfile))

    # Basics of creating a tiled and compressed geotiff
    cmd = [
        'gdalwarp',
        '-t_srs', 'EPSG:5070',
        '-r', 'bilinear',
    ]

    if extra_args is not None:
        cmd += extra_args

    cmd += [infile, outfile]

    logging.debug('run command: {}'.format(' '.join(cmd)))

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    out, err = p.communicate()

    return outfile


# Iterate over the list with this
def get_productname(product, datetime):
    if product == "nohrsc_snodas_swe_interpolated":
        return f"nohrsc_snodas_swe_interpolated_16_{datetime.strftime('%Y%m%d')}.tif"
    elif product == "nohrsc_snodas_swe":
        return f"zz_ssmv11034tS__T0001TTNATS{datetime.strftime('%Y%m%d')}05HP001_cloud_optimized.tif"

# Output format for content in the JSON file


def format_properties(obj):
    return {
        "HU_10": obj['HU_10_NAME'],
        "HU_10_NAME": obj['HU_10_NAME'],
        "min_inches": mm_to_inches(obj['min']),
        "max_inches": mm_to_inches(obj['max']),
        "mean_inches": mm_to_inches(obj['mean']),
        "count": obj['count']
    }


def mm_to_inches(mm):
    try:
        inches = round(mm * 0.0393701, 3)
        return inches
    except:
        return "NA"


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--start', required=True, help="Date to start file checks in YYYYMMDD")
    parser.add_argument('--end', required=True, help="Date to end file checks in YYYYMMDD")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s; %(levelname)s; %(message)s')

    # Set Start Time
    dtstart = datetime.strptime(args.start, '%Y%m%d')
    # Set End Time
    dtend = datetime.strptime(args.end, '%Y%m%d')

    # Where to get the raster information
    base_url = "https://cwbi-cumulus.s3.us-east-1.amazonaws.com/apimedia/products"
    product = "nohrsc_snodas_swe_interpolated"

    # Name the Output File
    outfile = f'statistics__{product}__{dtstart.strftime("%Y%m%d")}_to_{dtend.strftime("%Y%m%d")}.json'

    datetimes = []
    while dtstart < dtend:
        datetimes.append(dtstart)
        dtstart += timedelta(days=1)

    results = {}
    for dt in datetimes:

        try:
            # Clock is ticking
            _tstart = timer()

            raster = f'{base_url}/{product}/{get_productname(product, dt)}'
            logging.info(f'processing raster: {raster}')

            with tempfile.TemporaryDirectory(prefix=uuid4().__str__()) as td:

                # Warp file to EPSG:5070 (Equal Area Projection)
                _tstart_download_warp = timer()
                out_filename = f'{product}_{dt.strftime("%Y_%m_%d")}_EPSG5070.vrt'
                # outfile_shg = warp_to_vrt(f'/vsicurl/{raster}', os.path.join(td, out_filename))
                outfile_shg = warp_to_vrt(f'/vsicurl/{raster}', os.path.join(td, out_filename), extra_args=[
                                          '-te', '-356000', '2494000', '150000', '2950000', '-te_srs', 'EPSG:5070', '-tr', '1000', '1000'])
                _tend_download_warp = timer()

                # Area Statistics
                _tstart_stats = timer()
                shapefile = os.path.join("./", "misc", "REDRIVER_HUC10_EPSG5070.shp")
                zs = zonal_stats(shapefile, outfile_shg, stats=["min", "max", "mean", "count", ], geojson_out=True)
                _tend_stats = timer()

            # Save Area Statistics to JSON
            datetime_string = dt.strftime("%Y_%m_%d")
            datetime_results = {
                "time_sec_download_warp": round(_tend_download_warp - _tstart_download_warp),
                "time_sec_stats": round(_tend_stats - _tstart_stats),
                "result": {shape['properties']['HU_10_NAME']: format_properties(shape['properties']) for shape in zs},
            }
            results[datetime_string] = datetime_results

            # Write JSON Statistics File for Single Day
            with open(os.path.join('/var/www/html/statistics_redriver', f'statistics__{product}__{dt.strftime("%Y%m%d")}.json'), 'w') as day_outfile:
                day_outfile.write(
                    json.dumps(datetime_results, separators=(",", ":"))
                )
        except:
            logging.error(f'Could not compute zonal_statistics; product: {product}; date: {dt.strftime("%Y%m%d")}')

    # Write JSON Statistics File for Entire Run
    with open(os.path.join('/var/www/html/statistics_redriver', outfile), 'w') as outfile:
        outfile.write(
            json.dumps(results, separators=(",", ":"))
        )
