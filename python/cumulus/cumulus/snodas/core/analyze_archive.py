import argparse
import datetime
import gzip
import logging
import os
import re
import tarfile
import tempfile
from timeit import default_timer as timer
# https://stackoverflow.com/questions/7370801/measure-time-elapsed-in-python

import config
from .helpers import (
    snodas_get_raw_infile
)


def headerfile_content_from_raw_archive(infile, headerfile_name):
    """Extract headerfile for Snow Water Equivalent (SWE) based on

    <input file>        Path to the raw .tar SNODAS archive for a given day
    <headerfile_name>   Name of file to extract from raw archive
    """  

    with tarfile.open(infile) as tar:
        with tar.extractfile(headerfile_name) as gz_headerfile:
            with gzip.open(gz_headerfile, 'rt') as headerfile:
                content = headerfile.read()
    
    return content


def snodas_get_headerfile_values(headerfile_content):
    """Strip needed geospatial parameters out of the .txt file to analyze how they have changed over time
    """

    keywords = {
        'cols': {
            'keyword': 'Number of columns',
            'value': None
        },
        'rows': {
            'keyword': 'Number of rows',
            'value': None
        },
        'nodata': {
            'keyword': 'No data value',
            'value': None
        },
        'xmin': {
            'keyword': 'Minimum x-axis coordinate',
            'value': None
        },
        'xmax': {
            'keyword': 'Maximum x-axis coordinate',
            'value': None
        },
        'ymin': {
            'keyword': 'Minimum y-axis coordinate',
            'value': None
        },
        'ymax': {
            'keyword': 'Maximum y-axis coordinate',
            'value': None
        },
    }


    for k,v in keywords.items():
        # Why use re.compile()?
        # https://docs.python.org/3/library/re.html#re.compile
        pattern = re.compile('{}:\s+(\S*)\s+'.format(v['keyword']))
        result = pattern.search(content)
        if result is not None:
            keywords[k]['value'] = result.group(1)
    
    return {k: v['value'] for k, v in keywords.items()}


def swe_headerfile_name(dt, infile_type):
    """Return SWE headerfile name for a given datetime"""

    dtstr = dt.strftime('%Y%m%d')

    if infile_type.upper() == 'UNMASKED':
        return 'zz_ssmv11034tS__T0001TTNATS{}05HP001.txt.gz'.format(dtstr)
    elif infile_type.upper() == 'MASKED':
        return 'us_ssmv11034tS__T0001TTNATS{}05HP001.txt.gz'.format(dtstr)


def get_raw_infile_dict(dt_start, dt_end, infile_type):
    """List of RAW SNODAS files between dates dt_start and dt_end
    NOTE: List of infiles will eventually be retrieved from the database.
    """

    infiles = {}
    
    while dt_start < dt_end:
        infiles[dt_start] = get_raw_infile(dt_start, infile_type)
        dt_start += datetime.timedelta(days=1)
    
    return infiles


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="""Utility to extract SNODAS file metadata (upper-left, lower-right, nodata value)
        from SNODAS's custom .txt metadata files. This utility is also helpful for checking for missing data
        in a downloaded archive of SNODAS files
        """
    )
    parser.add_argument('--infile-type', required=True, choices=['masked', 'unmasked', ])
    parser.add_argument('--start', required=True, help="Date to start file checks in YYYYMMDD")
    parser.add_argument('--end', required=True, help="Date to end file checks in YYYYMMDD")
    parser.add_argument('--outfile', required=True, help="Path to output log")
    args = parser.parse_args()

    start = timer()

    # Configure logger
    logging.basicConfig(level=config.LOGLEVEL, format='%(asctime)s; %(levelname)s; %(message)s')

    raw_infiles = get_raw_infile_dict(
        datetime.datetime.strptime(args.start, '%Y%m%d'),
        datetime.datetime.strptime(args.end, '%Y%m%d'),
        args.infile_type
    )

    for dt, raw_infile in raw_infiles.items():

        if os.path.isfile(raw_infile):
            logging.debug('Working on file: {}'.format(raw_infile))

            try:
                content = headerfile_content_from_raw_archive(raw_infile, swe_headerfile_name(dt, args.infile_type))
            except:
                logging.critical('Could not extract headerfile for date: {}'.format(dt))
                continue

            values = snodas_get_headerfile_values(content)

            values_as_csv = ','.join(
                [dt.strftime('%Y%m%d'), ] + list(values.values())
            )

            with open(args.outfile, 'a') as f:
                f.write('{}\n'.format(values_as_csv))
        
        else:
            logging.warning('Missing File: {}'.format(raw_infile))
    
    finish = timer()
    
    print('Done in {}'.format(finish - start))
