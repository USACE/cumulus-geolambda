#!/usr/env python3

# Description

# The process requires 3 high-level steps:

# High-level steps
#
# 1) Apply "Lakefix"
# 2) Interpolate values over waterbodies using bilinear interpolation
# 3) Restore legitimate nodata cells from original input dataset not located over waterbodies.

# Details
#
# Lakefix: Need to apply the lakefix is based on the date of the file and the variable code (1034 and 1036), which correspond to Snow Water Equivalent and Snow Depth
#          Some of the values around lakes have been set to 0. They are not necessarily 0, but are more appropriately "nodata".
#          "Lakefix" is the process of setting these 0 cells to nodata and requires 2 steps:
#          (1) Set values in the "nodata" areas specified by a Mask Raster to "-9999"
#          (2) Set values of "-9999" to nodata. This is required so interpolation works

# Interpolation:
import datetime
import logging
import os
import numpy as np
from osgeo import gdal, gdal_array
from pytz import utc
import subprocess


def file_needs_lakefix(process_date, varcode):
    '''Helper function to determine whether to run lakefix_zero_values_to_nodata.

    Lakefix is required for Snow Water Equivalent (SWE) (1034) and Snow Depth (1036)
    '''

    # varcode passed as string in main(); however, explicitly convert varcode 
    # to a string in case varcode is passed an int.
    varcode = str(varcode)

    if (process_date >= datetime.datetime(2014, 10, 9, 0, 0, tzinfo=utc) and (varcode == "1034" or varcode == "1036")):
        return True
    else:
        return False


def lakefix_zero_values_to_nodata(infile, outfile, nodata_val, mask_raster):
    ''' tbb, 11/26/2018
    For SWE and snow depth, need to set additional no-data values around lakes.
    These two parameters have set some pixels to 0 where they should be no-data.
    This started to occur on Oct 9, 2014.
    This works on command line:
        gdal_calc.py -A zz_ssmv11034tS__T0001TTNATS2018030605HP001.bil
                     -B no_data_areas_swe_20140201.tif
                     --calc="numpy.where((A == 0) & (B == -9999), -9999, A)"
                     --NoDataValue=-9999 --outfile gc3.tif
    '''

    # Subprocess command
    cmd = ['gdal_calc.py', '-A', infile, '-B', mask_raster, '--calc', 'numpy.where((A == 0) & (B == -9999), -9999, A)', '--NoDataValue', nodata_val, '--outfile', outfile]
    logging.debug(' '.join(cmd))
    result = subprocess.check_call(cmd)
    logging.debug(result)

    return outfile


def lakefix_set_cells_to_nodata(file_after_fill, file_before_fill, swe_nodata_filled):
    '''Reset valid NoData cells to NoData based on raster dataset inputs. Write directly to <file_after_fill>.
    <file_after_fill> File to be modified. Snowpack average temperature (1038) or snowmelt (1044) after fill_nodata_values()
    <file_before_fill> File (original). Before set_value_to_nodata().
    <swe_nodata_filled> SWE after lakefix_zero_values_to_nodata(), set_value_to_nodata(), and fill_nodata_values() have been run.
    For snowpack average temperature (1038) and snowmelt (1044):
        If file_before_fill=nodata & swe_nodata_filled=0 --> set file_after_fill=nodata
    '''

    def get_band_info(infile):
        _ds = gdal.Open(infile, gdal.GA_ReadOnly)
        _info = {
            'size_x': _ds.RasterXSize,
            'size_y': _ds.RasterYSize,
            'datatype': _ds.GetRasterBand(1).DataType,
            'nodata': _ds.GetRasterBand(1).GetNoDataValue(),
        }
        _ds = None
        
        return _info

    def write_arr_to_tiff(outfile, arr):
        '''Helper function to write array to TIF file
        Writing to an already existing raster, so the function references the
        Band in the raster before overwriting it to get xsize, ysize, datatype, nodata
        '''

        ds = gdal.Open(outfile, gdal.GA_ReadOnly)
        _nodata = ds.GetRasterBand(1).GetNoDataValue()
        
        driver = gdal.GetDriverByName("GTiff")
        dsout = driver.Create(
            outfile,
            ds.RasterXSize,
            ds.RasterYSize,
            1,
            ds.GetRasterBand(1).DataType,
            options=['COMPRESS=LZW']
        )
        dsout.SetGeoTransform(ds.GetGeoTransform())
        dsout.SetProjection(ds.GetProjection())
        dsout.GetRasterBand(1).SetNoDataValue(_nodata)
        dsout.GetRasterBand(1).WriteArray(arr)
        dsout.FlushCache()
        dsout.GetRasterBand(1).GetStatistics(0, 1)

        ds = None
        driver = None
        dsout = None

        return outfile

    # Data Arrays
    swe = gdal_array.LoadFile(swe_nodata_filled)             # SWE
    logging.debug(f'SWE; {swe_nodata_filled} ; {swe}')
    arr_before_fill = gdal_array.LoadFile(file_before_fill)  # File Before Fill
    logging.debug(f'File Before Fill; {file_before_fill} ; {arr_before_fill}')
    arr_after_fill = gdal_array.LoadFile(file_after_fill)    # File After Fill
    logging.debug(f'File After Fill; {file_after_fill} ; {arr_after_fill}')

    # compare datasets size_y
    logging.debug(f'size_y of arrays: {len(swe)}; {len(arr_before_fill)}; {len(arr_after_fill)}')
    if len(swe) != len(arr_before_fill) != len(arr_after_fill):
        logging.critical(f'Datasets do not have the same size_y!')
        return None
    # compare datasets size_x
    logging.debug(f'size_x of arrays: {len(swe[0])}; {len(arr_before_fill[0])}; {len(arr_after_fill[0])}')
    if len(swe[0]) != len(arr_before_fill[0]) != len(arr_after_fill[0]):
        logging.critical(f'Datasets do not have the same size_x!')
        return None
    
    # Get nodata value for computations
    nodata = get_band_info(swe_nodata_filled)['nodata']
    logging.debug(f'nodata value: {nodata}')

    # Output Array
    out_arr = np.where((swe == 0) & (arr_before_fill == nodata), nodata, arr_after_fill)
    logging.debug(f'Output Array; {out_arr}')

    # Write Array to TIF
    _outfile = write_arr_to_tiff(file_after_fill, out_arr)
    logging.debug(f'Output File: {_outfile}')

    return _outfile
