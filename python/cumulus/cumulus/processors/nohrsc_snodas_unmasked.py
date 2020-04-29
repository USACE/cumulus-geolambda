from datetime import datetime
import os
import re

from ..snodas.core.process import process_snodas_for_date


def process(infile, outdir):
    """Takes an infile to process and path to a directory where output files should be saved
    Returns array of objects [{ "filetype": "nohrsc_snodas_swe", "file": "file.tif", ... }, {}, ]
    """

    def get_file_date():
        """Helper function to strip date from the filename"""
        m = re.match(r"SNODAS_unmasked_([0-9]+).tar", os.path.basename(infile))
    
        if m is not None:
            return datetime.strptime(m[1], '%Y%m%d')
        
        return None
    
    # Fail fast if date can not be determined
    dt = get_file_date()
    if dt is None:
        return []

    outfile_dict = process_snodas_for_date(dt, infile, 'UNMASKED', outdir)

    # Probably better to implement this in the snodas/core later
    outfile_list = []
    for k, v in outfile_dict.items():
        outfile_list.append({"file": v, "filetype": k, "datetime": dt.isoformat()})
    #

    return outfile_list
