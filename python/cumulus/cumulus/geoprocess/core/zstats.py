import argparse
from datetime import datetime, timedelta
import shapely
import json
import os
from rasterstats import zonal_stats
import subprocess
from tempfile import TemporaryDirectory
from timeit import default_timer as timer
from uuid import uuid4

from pytz import utc

from .base import warp
from .helpers import buffered_extent

def zstats_generic(raster, vector):

    with TemporaryDirectory(prefix=uuid4().__str__()) as td:

        # Get vector extent so we can minimize download to minimum bounding rectangle
        # Missouri River to Test: "x_min":-1394000,"y_min":1552000,"x_max":510000,"y_max":3044000,
        minx, miny, maxx, maxy = buffered_extent(
            [-1394000, 1552000, 510000, 3044000], 2, 2000
        )
        
        # Warp file to EPSG:5070 (Equal Area Projection)
        _tstart_download_warp = timer()
        outfile_shg = warp(raster, os.path.join(td, f'_raster_EPSG5070.tif'), extra_args=[
            '-t_srs', 'EPSG:5070', '-r', 'bilinear', '-te', minx, miny, maxx, maxy, '-te_srs', 'EPSG:5070', '-tr', '1000', '1000',
            '--config', 'GDAL_HTTP_UNSAFESSL', 'YES',
            ]
        )
        _tend_download_warp = timer()

        # Area Statistics
        _tstart_stats = timer()
        zs = zonal_stats(
            vector,
            outfile_shg,
            stats=["min", "max", "mean", "count", ],
            geojson_out=True
        )
        _tend_stats = timer()

    return {
        "time_sec_download_warp": round(_tend_download_warp - _tstart_download_warp),
        "time_sec_stats": round(_tend_stats - _tstart_stats),
        "result": zs,
    }
