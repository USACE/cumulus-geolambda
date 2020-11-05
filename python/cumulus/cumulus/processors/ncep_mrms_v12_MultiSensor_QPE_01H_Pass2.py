from datetime import datetime
import os
from uuid import uuid4
from ..geoprocess.core.base import info, translate, create_overviews

def process(infile, outdir):
    """Takes an infile to process and path to a directory where output files should be saved
    Returns array of objects [{ "filetype": "nohrsc_snodas_swe", "file": "file.tif", ... }, {}, ]
    """

    # Only Get Air Temperature to Start; Band 3 (i.e. array position 2 because zero-based indexing)
    dtStr = info(f'/vsigzip/{infile}')['bands'][0]["metadata"][""]['GRIB_VALID_TIME']

    # Get Datetime from String Like "1599008400 sec UTC"
    dt = datetime.fromtimestamp(int(dtStr.split(" ")[0]))

    # Extract Band 0 (QPE); Convert to COG
    tif = translate(f'/vsigzip/{infile}', os.path.join(outdir, f"temp-tif-{uuid4()}"))
    tif_with_overviews = create_overviews(tif)
    cog = translate(
        tif_with_overviews,
        os.path.join(
            outdir,
            "{}.tif".format(
                os.path.basename(infile).split(".grib2.gz")[0]
            )
        )
    )

    outfile_list = [
        { "filetype": "ncep_mrms_v12_MultiSensor_QPE_01H_Pass2", "file": cog, "datetime": dt.isoformat()},
    ]

    return outfile_list
