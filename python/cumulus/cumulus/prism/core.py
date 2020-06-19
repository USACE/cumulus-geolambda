from datetime import datetime
import os
import re


def prism_datetime_from_filename(infile):
    """Helper function to return datetime from a prism-formatted filename
    Works on file absolute path, relative path, or simple filename
    """
    
    pattern = r"PRISM_[a-z]+_early_4kmD2_([0-9]+)_bil.zip"
    
    m = re.match(pattern, os.path.basename(infile))
    if m is not None:
        return datetime.strptime(m[1], '%Y%m%d')
    
    return None
