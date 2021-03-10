from datetime import datetime
import os
from uuid import uuid4
from ..geoprocess.core.base import info, translate, create_overviews

import json

def process(infile, outdir):
    """Takes an infile to process and path to a directory where output files should be saved
    Returns array of objects [{ "filetype": "nohrsc_snodas_swe", "file": "file.tif", ... }, {}, ]
    """

    fileinfo = info(infile)
    print(json.dumps(fileinfo, indent=2))
    for band in fileinfo["bands"]:
        band_number = str(band["band"])
        band_meta = band["metadata"][""]
        dtStr = band_meta["GRIB_VALID_TIME"]
        if "Temperature [C]" in band_meta["GRIB_COMMENT"]: break

    # dtStr = info(infile)['bands'][1]["metadata"][""]['GRIB_VALID_TIME']

    # Get Datetime from String Like "1599008400 sec UTC"
    dt = datetime.fromtimestamp(int(dtStr.split(" ")[0]))

    print(f"Band number is {band_number}, date string is {dtStr}, and date is {dt}")

    # # Extract Band 0 (QPE); Convert to COG
    tif = translate(infile, os.path.join(outdir, f"temp-tif-{uuid4()}"), extra_args=["-b", band_number])
    tif_with_overviews = create_overviews(tif)
    cog = translate(
        tif_with_overviews,
        os.path.join(
            outdir,
            "{}.tif".format(
                os.path.basename(infile)
            )
        )
    )

    outfile_list = [
        { "filetype": "ndgd_ltia98_airtemp", "file": cog, "datetime": dt.isoformat(), "version": None },
    ]

    return outfile_list
