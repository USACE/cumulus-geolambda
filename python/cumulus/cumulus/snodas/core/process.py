#!/usr/env python3

import argparse
import datetime
import numpy as np
from osgeo import gdal
import gzip
import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile


from ...geoprocess.core.base import (
    create_overviews,
    scale_raster_values,
    translate,
    write_array_to_raster
)

from ...handyutils.core import (
    gunzip_file,
    change_file_extension,
    delete_files_by_extension,
    mkdir_p
)

# snodas module
from .helpers import snodas_get_headerfile


def snodas_filename_prefix(infile_type):
    
    if infile_type.upper() == 'UNMASKED':
        return 'zz'
    elif infile_type.upper() == 'MASKED':
        return 'us'


def snodas_filenames(datetime, infile_type):
    """Return a dictionary of SNODAS filenames for a given datetime"""

    dtstr = datetime.strftime('%Y%m%d')

    prefix = snodas_filename_prefix(infile_type)

    filenames = {
        'nohrsc_snodas_swe': '{}_ssmv11034tS__T0001TTNATS{}05HP001',
        'nohrsc_snodas_snowdepth': '{}_ssmv11036tS__T0001TTNATS{}05HP001',
        'nohrsc_snodas_snowpack_average_temperature': '{}_ssmv11038wS__A0024TTNATS{}05DP001',
        'nohrsc_snodas_snowmelt': '{}_ssmv11044bS__T0024TTNATS{}05DP000',
    }

    return {k: v.format(prefix, dtstr) for k, v in filenames.items()}


def computed_filenames(datetime, infile_type):

    dtstr = datetime.strftime('%Y%m%d')
    prefix = snodas_filename_prefix(infile_type)

    return {
        'nohrsc_snodas_coldcontent': '{}_coldcontent_{}'.format(prefix, dtstr),
        'nohrsc_snodas_snowmeltmm': '{}_snowmeltmm_{}'.format(prefix, dtstr)
    }


def snodas_write_coldcontent(snowpack_average_temperature, snow_water_equivalent, outfile):

    # snowpack_average_temperature dataset
    snowtemp_ds = gdal.Open(snowpack_average_temperature, gdal.GA_ReadOnly)
    xsize = snowtemp_ds.RasterXSize
    ysize = snowtemp_ds.RasterYSize
    geotransform = snowtemp_ds.GetGeoTransform()
    projection = snowtemp_ds.GetProjection()

    # snowpack_average_temperature as a band
    snowtemp_band = snowtemp_ds.GetRasterBand(1)
    nodata_value = snowtemp_band.GetNoDataValue()

    # snowpack_average_temperature as an array
    snowtemp_array = snowtemp_band.ReadAsArray(0, 0, xsize, ysize).astype(np.dtype('float32'))

    # snow_water_equivalent dataset
    swe_ds = gdal.Open(snow_water_equivalent, gdal.GA_ReadOnly)

    # snow_water_equivalent array
    # Note: Must have same boundaries and cell size as snowpack_average_temperature
    swe_array = swe_ds.GetRasterBand(1).ReadAsArray(0, 0, xsize, ysize).astype(np.dtype('float32'))
    
    # Convert snowpack_average_temperature to degrees Celsius
    snowtemp_array_degc = np.where(snowtemp_array == nodata_value, nodata_value, snowtemp_array - 273.15)

    # computed coldcontent_array
    coldcontent_array = np.where(
        snowtemp_array_degc >= 0, 0,
        np.where((swe_array == nodata_value) | (snowtemp_array_degc == nodata_value), nodata_value, swe_array * 2114 * snowtemp_array_degc / 333000)
    )

    # Write numpy array to TIF
    coldcontent_raster = write_array_to_raster(coldcontent_array, outfile, xsize, ysize, geotransform, projection, gdal.GDT_Float32, nodata_value)

    # make sure to free-up memory
    snowtemp_ds = None
    xsize = None
    ysize = None
    geotransform = None
    projection = None
    snowtemp_band = None
    nodata_value = None
    snowtemp_array = None
    swe_ds = None
    swe_array = None
    snowtemp_array_degc = None
    coldcontent_array = None

    return coldcontent_raster


def snodas_translate_args(dt, infile_type):

    def get_ullr(dt, infile_type):
        """UpperLeft/LowerRight of dataset has changed over time 
        and is a function of when the snodas grids were produced.

        For unmasked dataset:

            2009-12-09 (start of dataset) to 2013-09-30 (including 30th) : [-130.517083333332, 58.2329166666655, -62.2504166666677, 24.0995833333335]
            2013-10-01 - 2017-08-23 (including 23rd) :                     [-130.516666666662, 58.2333333333310, -62.2499999999977, 24.0999999999990]
            2017-08-24 - 2019-08-20 (present)                              [-130.516666666661, 58.2333333333310, -62.2499999999975, 24.0999999999990]

            Note: The 2017 shift in the "x" by ~ 0.000000000001 will be disregarded because the difference is far enough to the right of the decimal point 
            and should not make a difference. The ULLR values in use at 2019-08-20 will be applied to all transoformations from 2013-10-01 forward (to present)

        For masked dataset:

            2003-09-30 - 2006-03-29: [-124.733749999998366, 52.874583333332339, -66.942083333334011, 24.949583333333454]
            2006-03-30 - 2006-06-18: [-124.733749999998   , 52.8745833333323  , -66.9420833333340  , 24.9495833333335  ]
            2006-06-19 - 2006-09-10: [-124.733749999999   , 52.8745833333323  , -66.9420833333342  , 24.9495833333335  ]
            2006-09-11 - 2009-06-25: [-124.733749999999   , 52.8745833333322  , -66.9420833333342  , 24.9495833333334  ]
            2006-06-26 - 2009-07-02: [-124.733749999998   , 52.8745833333323  , -66.9420833333340  , 24.9495833333334  ]
            2009-07-03 - 2009-12-31: [-124.733749999999   , 52.8745833333322  , -66.9420833333342  , 24.9495833333334  ]
            Note: 2009-12-31 is last day checked, because we use the unmasked dataset when it becomes available in December 2009

            The minor fluxuations in the ULLR metadata are far enough to the right of the decimal point and the guidance from the NSIDC website will be used
            to assign ULLR coordinates.  Website content copied below for convenience: https://nsidc.org/support/how/how-do-i-convert-snodas-binary-files-geotiff-or-netcdf

            Appendix 2. Spatial bounds to feed into GDAL -ullr flag for pre and post Oct 01 2013.

            Pre Oct 01 2013: -124.73375000 52.87458333 -66.94208333 24.87458333

            Post Oct 01 2013: -124.73333333 52.87500000 -66.94166667 24.95000000
        """

        # Unmasked dataset
        if infile_type.upper() == 'UNMASKED':
            if dt < datetime.datetime(2013, 10, 1):
                ullr = [-130.517083333332, 58.2329166666655, -62.2504166666677, 24.0995833333335]
            else:
                ullr = [-130.516666666661, 58.2333333333310, -62.2499999999975, 24.0999999999990]
        
        elif infile_type.upper() == 'MASKED':
            if dt < datetime.datetime(2013, 10, 1):
                ullr = [-124.73375000, 52.87458333, -66.94208333, 24.87458333]
            else:
                ullr = [-124.73333333, 52.87500000, -66.94166667, 24.95000000]


        return [str(v) for v in ullr]


    args = [
        '-a_srs', '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs',
        '-a_nodata', '-9999',
        '-a_ullr', ] + get_ullr(dt, infile_type)
    
    return args


def prepared_file_from_tarfile(tar, filename, outdir, infile_type):
    """Extract a single file from a .tar, transform it into a format GDAL can
    work with, and return the absolute filepath
    """
    # Extract .dat.gz file
    with tarfile.open(tar) as _tar:
        outfile = _tar.extract(f'{filename}.dat.gz', path=outdir)
       
    # Unzip file and rename ".dat" extension to ".bil"
    gunzip_file(
        os.path.join(outdir, f'{filename}.dat.gz'),
        os.path.join(outdir, change_file_extension(f'{filename}.dat', 'bil'))
    )
    # Delete .dat.gz file, it is no longer needed
    os.remove(os.path.join(outdir, f'{filename}.dat.gz'))

    # Write appropriate .hdr file in same directory, same root name as .bil file
    shutil.copy(
        snodas_get_headerfile(infile_type),
        os.path.join(outdir, change_file_extension(f'{filename}.dat', 'hdr'))
    )

    return os.path.abspath(os.path.join(outdir, f'{filename}.bil'))


def process_snodas_for_date(dt, infile, infile_type, outdir):

    def path_factory(directory, file_format, filename_base=None):
        """Generate a unique absolute path for intermediate processing files

        <directory>     Parent directory (i.e. dirname) for <file_format>/<filename_base>.tif
        <file_format>   Accepts tif and cog, case insensitive
        <filename_base> Name of file without file extension.
            Default Value: None  - intended to return path to a directory

        """

        if file_format.upper() == 'TIF':
            return os.path.join(directory, 'tif', '{}.tif'.format(filename_base))
        elif file_format.upper() == 'COG':
            return os.path.join(directory, 'cog', '{}_cloud_optimized.tif'.format(filename_base))
        elif file_format.upper() == 'RAW':
            return os.path.join(directory, 'raw')


    def add_to_outdict_if_exists(infile, keyword, outdict):
        """Check if a file exists. If so, add it to the provided dictionary
        """
        if os.path.isfile(infile):
            outdict[keyword] = infile


    # Keep track of files that are processed
    processed_files = {}

    # Make temporary directories for processing
    [mkdir_p('{}/{}'.format(outdir, td)) for td in ('tif', 'cog', 'raw')]

    for parameter, filename in snodas_filenames(dt, infile_type).items():
        logging.debug(f'working on parameter: {parameter}; filename: {filename}')

        # extract the raw file of interest into something gdal can work with
        _file = prepared_file_from_tarfile(
            infile,
            filename,
            os.path.join(outdir, "raw"),
            infile_type
        )

        # NATIVE COORDINATE SYSTEM
        # ========================
        # (1) Save TIF file (translate) (2) Create overviews (pyramids) (3) Save Cloud Optimized Geotiff (translate)
        outfile = translate(_file, path_factory(outdir, 'tif', filename), extra_args=snodas_translate_args(dt, infile_type))
        create_overviews(outfile)
        outfile_cog = translate(outfile, path_factory(outdir, 'cog', filename))
        # Add tif and cloud optimized geotiff to list of outfiles if they were created
        add_to_outdict_if_exists(outfile_cog, parameter, processed_files)
        # Delete tif after cloud optimized geotiff is created
        os.remove(outfile)
    
    # Delete snodas raw .tar file
    os.remove(infile)

    # -------------------------------------------------------------------
    # COMPUTE COLD CONTENT GRID FROM SWE AND SNOWPACK AVERAGE TEMPERATURE
    # -------------------------------------------------------------------
    coldcontent = snodas_write_coldcontent(
        path_factory(outdir, 'cog', snodas_filenames(dt, infile_type)['nohrsc_snodas_snowpack_average_temperature']),
        path_factory(outdir, 'cog', snodas_filenames(dt, infile_type)['nohrsc_snodas_swe']),
        path_factory(outdir, 'tif', computed_filenames(dt, infile_type)['nohrsc_snodas_coldcontent'])
    )
    # Overviews
    create_overviews(coldcontent)
    # Cloud Optimized Geotiff
    coldcontent_cog = translate(
        coldcontent,
        path_factory(outdir, 'cog', computed_filenames(dt, infile_type)['nohrsc_snodas_coldcontent']),
    )
    # Add tif and cloud optimized geotiff to list of outfiles if they were created
    add_to_outdict_if_exists(coldcontent_cog, 'nohrsc_snodas_coldcontent', processed_files)

    # Delete tif after cloud optimized geotiff is created
    os.remove(coldcontent)

    # ----------------------------------------------------------------
    # COMPUTE SNOWMELT IN MILLIMETERS (UNIT CONVERSION ON SNODAS GRID)
    # ----------------------------------------------------------------
    # Snowmelt in Millimeters, Native Projection
    snowmeltmm = scale_raster_values(
        0.01,
        path_factory(outdir, 'cog', snodas_filenames(dt, infile_type)['nohrsc_snodas_snowmelt']),
        path_factory(outdir, 'tif', computed_filenames(dt, infile_type)['nohrsc_snodas_snowmeltmm'])
    )
    # Overviews
    create_overviews(snowmeltmm)
    # Cloud Optimized Geotiff
    snowmeltmm_cog = translate(
        snowmeltmm,
        path_factory(outdir, 'cog', computed_filenames(dt, infile_type)['nohrsc_snodas_snowmeltmm']),
    )

    # Add tif and cloud optimized geotiff to list of outfiles if they were created
    add_to_outdict_if_exists(snowmeltmm_cog, 'nohrsc_snodas_snowmelt', processed_files)

    # Delete tif after cloud optimized geotiff is created
    os.remove(snowmeltmm)

    return processed_files
