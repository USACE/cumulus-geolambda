import argparse
from datetime import datetime, timedelta
import fiona
import json
import os
from rasterstats import zonal_stats
import subprocess
from tempfile import TemporaryDirectory
from timeit import default_timer as timer
from uuid import uuid4

from pytz import utc

from products.models import ProductFile
from cumulus.handyutils.core import write_json_to_file

from .base import warp
from .helpers import buffered_extent

# THIS SCRIPT SHOULD BE GENERALIZED IN THE FUTURE WHEN POSSIBLE
# BEWARE OF HARD-CODING LIKE "/var/www/html"

def zstats_generic(raster, shapefile):

    def format_properties(obj):
        """Helper function to format JSON response natively returned by rasterstats"""
        return {
            "name": obj['Name'],
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


    with TemporaryDirectory(prefix=uuid4().__str__()) as td:

        # Get shapefile extent so we can minimize download to minimum bounding rectangle
        with fiona.open(shapefile) as shp:
            minx, miny, maxx, maxy = buffered_extent(shp.bounds, 2, 2000)
        
        # Warp file to EPSG:5070 (Equal Area Projection)
        _tstart_download_warp = timer()
        outfile_shg = warp(f'/vsicurl/{raster}', os.path.join(td, f'_raster_EPSG5070.tif'), extra_args=[
            '-t_srs', 'EPSG:5070', '-r', 'bilinear', '-te', minx, miny, maxx, maxy, '-te_srs', 'EPSG:5070', '-tr', '1000', '1000',
            '--config', 'GDAL_HTTP_UNSAFESSL', 'YES',
            ]
        )
        _tend_download_warp = timer()

        # Area Statistics
        _tstart_stats = timer()
        zs = zonal_stats(
            os.path.abspath(shapefile),
            outfile_shg,
            stats=["min", "max", "mean", "count", ],
            geojson_out=True
        )
        _tend_stats = timer()

    return {
        "time_sec_download_warp": round(_tend_download_warp - _tstart_download_warp),
        "time_sec_stats": round(_tend_stats - _tstart_stats),
        "result": {shape['properties']['Name']: format_properties(shape['properties']) for shape in zs},
    }


def zstats_redriver(raster):
    """Uses raster and vectors (shapefile) to compute statistics.  Returns JSON."""

    def format_properties(obj):
        """Helper function to format JSON response natively returned by rasterstats"""
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

    # Clock is ticking
    _tstart = timer()

    with TemporaryDirectory(prefix=uuid4().__str__()) as td:

        # Warp file to EPSG:5070 (Equal Area Projection)
        _tstart_download_warp = timer()
        outfile_shg = warp(f'/vsicurl/{raster}', os.path.join(td, f'_raster_EPSG5070.tif'), extra_args=[
            '-t_srs', 'EPSG:5070', '-r', 'bilinear', '-te', '-356000', '2494000', '150000', '2950000', '-te_srs', 'EPSG:5070', '-tr', '1000', '1000',
            '--config', 'GDAL_HTTP_UNSAFESSL', 'YES',
        ]
        )
        _tend_download_warp = timer()

        # Area Statistics
        _tstart_stats = timer()
        zs = zonal_stats(
            # Shapefile; This is specific to the Red River of the North
            os.path.join("/app", "examples", "shapes", "REDRIVER_HUC10_EPSG5070.shp"),
            outfile_shg,                                                                # Raster
            stats=["min", "max", "mean", "count", ],
            geojson_out=True
        )
        _tend_stats = timer()

    # Save Area Statistics to JSON

    _result = {
        "time_sec_download_warp": round(_tend_download_warp - _tstart_download_warp),
        "time_sec_stats": round(_tend_stats - _tstart_stats),
        "result": {shape['properties']['HU_10_NAME']: format_properties(shape['properties']) for shape in zs},
    }

    return _result
