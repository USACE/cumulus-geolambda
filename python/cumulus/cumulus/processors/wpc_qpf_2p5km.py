from datetime import datetime
import os
from uuid import uuid4
from ..geoprocess.core.base import info, translate, create_overviews

def process(infile, outdir):
    """Takes an infile to process and path to a directory where output files should be saved
    Returns array of objects [{ "filetype": "wpc_qpf_2p5km", "file": "file.tif", ... }, {}, ]
    """

    # Date String
    dtStr = info(infile)['bands'][0]["metadata"][""]['GRIB_VALID_TIME']

    # Get Datetime from String Like "1599008400 sec UTC"
    dt = datetime.fromtimestamp(int(dtStr.split(" ")[0]))

    # Extract Band
    tif = translate(infile, os.path.join(outdir, f"temp-tif-{uuid4()}"))
    tif_with_overviews = create_overviews(tif)
    cog = translate(
        tif_with_overviews,
        os.path.join(
            outdir,
            "{}.tif".format(
                os.path.basename(infile).split(".grb")[0]
            )
        )
    )

    outfile_list = [
        { "filetype": "wpc_qpf_2p5km", "file": cog, "datetime": dt.isoformat()},
    ]

    return outfile_list
