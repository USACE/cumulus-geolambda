from datetime import datetime
import json
import os
import re

from ..geoprocess.core.base import info, translate, create_overviews
from ..prism.core import prism_datetime_from_filename
import zipfile


def process(infile, outdir):
    """Takes an infile to process and path to a directory where output files should be saved
    Returns array of objects [{ "filetype": "nohrsc_snodas_swe", "file": "file.tif", ... }, {}, ]
    """

    dt = prism_datetime_from_filename(infile)

    # See vsidriver chaining: https://gdal.org/user/virtual_file_systems.html
    bilfile = f'/vsizip/{infile}/{os.path.splitext(os.path.basename(infile))[0]}.bil'
       
    # Create GeoTIFF
    translated = translate(
        bilfile,
        os.path.join(outdir, "translated.tif")
    )
    # Create Overviews
    create_overviews(translated)
    # COG
    outfile_cog = translate(
        translated,
        os.path.join(outdir, "my_final_cog.tif"),
    )

    outfile_list = [
        { "filetype": "prism_ppt_early", "file": outfile_cog, "datetime": dt.isoformat()},
    ]

    return outfile_list
