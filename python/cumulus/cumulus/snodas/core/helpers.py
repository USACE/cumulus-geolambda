import datetime
import os
from pytz import utc

from .config import (
    SNODAS_APP,
    SNODAS_RAW_UNMASKED,
    SNODAS_RAW_MASKED
)


def snodas_get_raw_infile_name(dt, infile_type):

    dtstr = dt.strftime('%Y%m%d')

    if infile_type.upper() == 'UNMASKED':
        return 'SNODAS_unmasked_{}.tar'.format(dtstr)
    elif infile_type.upper() == 'MASKED':
        return 'SNODAS_{}.tar'.format(dtstr)


def snodas_get_raw_infile(dt, infile_type):

    filename = snodas_get_raw_infile_name(dt, infile_type)

    if infile_type.upper() == 'UNMASKED':
        return os.path.join(SNODAS_RAW_UNMASKED, filename)
    elif infile_type.upper() == 'MASKED':
        return os.path.join(SNODAS_RAW_MASKED, filename)


def snodas_get_headerfile(infile_type):
    """Return absolute path to appropriate .hdr file for SNODAS grids.
    Appropriate header depends on dataset (masked vs. unmasked) and
    resides in the same directory as this function
    """

    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), '{}.hdr'.format(infile_type.lower()))
    )


def snodas_get_nodata_value(process_date):
    '''Return value used by NOHRSC/SNODAS to represent "NoData"
    Return value based on datetime object for the date the file represents'''

    if process_date < datetime.datetime(2011, 1, 24, 0, 0, tzinfo=utc):
        return '55537'
    else:
        return '-9999'
