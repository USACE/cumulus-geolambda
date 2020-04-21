import os
import subprocess
import sys
import logging

# set up logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# commented out to avoid duplicate logs in lambda
logger.addHandler(logging.StreamHandler())

# imported to test loading of libraries
from osgeo import gdal
# import pyproj
# import rasterio
# import shapely

from datetime import datetime
import os
from urllib.parse import urlsplit
from urllib.request import urlretrieve
import tempfile

from cumulus.snodas.core.process import process_snodas_for_date


def get_infile():
    
    url = 'https://cwbi-cumulus.s3.amazonaws.com/apimedia/products/nohrsc_snodas_raw_unmasked/SNODAS_unmasked_20200420.tar'
    filename, headers = urlretrieve(url)
    
    return os.path.abspath(filename)


def lambda_handler(event, context=None):
    """ Lambda handler """

    # this try block is for testing and info only,
    # it prints out info on the the libgdal binary and paths to linked libraries
    #try:
    #    output = subprocess.check_output('readelf -d /opt/lib/libgdal.so'.split(' '))
    #    logger.info(output.decode())
    #    output = subprocess.check_output('ldd /opt/lib/libgdal.so'.split(' '))
    #    logger.info(output.decode())
    #except Exception as e:
    #    pass

    with tempfile.TemporaryDirectory() as td:
        infile, dt = get_infile(), datetime(year=2020, month=4, day=20)
        process_snodas_for_date(dt, infile, 'UNMASKED', td)
        filelist = os.listdir(os.path.join(td, "cog"))
    
    return filelist


if __name__ == "__main__":
    """ Test lambda_handler """
    # event = {'filename': test_filename}
    files = lambda_handler(event)
