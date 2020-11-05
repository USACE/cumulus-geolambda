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
            return datetime.strptime(m[1], '%Y%m%d') + datetime.timedelta(hours=6)
        
        return None
    
    # Fail fast if date can not be determined
    dt = get_file_date()
    if dt is None:
        return []

    outfile_list = process_snodas_for_date(dt, infile, 'UNMASKED', outdir)

    return outfile_list
