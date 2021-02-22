from datetime import datetime
from ..prism.core import prism_datetime_from_filename
from ..prism.core import prism_convert_to_cog


def process(infile, outdir):
    """Takes an infile to process and path to a directory where output files should be saved
    Returns array of objects [{ "filetype": "nohrsc_snodas_swe", "file": "file.tif", ... }, {}, ]
    """

    dt = prism_datetime_from_filename(infile)

    outfile_cog = prism_convert_to_cog(infile, outdir)

    outfile_list = [
        { "filetype": "prism_tmax_early", "file": outfile_cog, "datetime": dt.isoformat(), "version": None },
    ]

    return outfile_list
