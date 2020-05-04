import json
import logging
import os
import subprocess
import tempfile
from uuid import uuid4

from osgeo import gdal


def info(file):
    """Standard way of calling gdalinfo and returning a python dictionary of metadata"""

    cmd = ['gdalinfo', '-json', str(file)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)

    try:
        return json.loads(result.stdout)
    except Exception as e:
        logging.error(f'gdalinfo fail: {" ".join(cmd)}; {e}')
        return {}


def write_array_to_raster(array, outfile, xsize, ysize, geotransform, projection, datatype, nodata_value):

    dsout = gdal.GetDriverByName('GTiff').Create(
        outfile, xsize, ysize, 1, datatype,
        options=[
            'COMPRESS=DEFLATE',
            'TILED=YES'
        ]
    )
    dsout.SetGeoTransform(geotransform)
    dsout.SetProjection(projection)
    dsout.GetRasterBand(1).SetNoDataValue(nodata_value)
    dsout.GetRasterBand(1).WriteArray(array)
    dsout.FlushCache()
    dsout.GetRasterBand(1).GetStatistics(0, 1)

    return outfile


def get_array_from_raster_old(infile, str_datatype):
    '''Returns a list of required parameters from supplied <infile> and <str_datatype> to define array'''

    logging.info('Get Array From Raster: {}'.format(infile))
    ds = gdal.Open(infile, gdal.GA_ReadOnly)
    size_x = ds.RasterXSize
    size_y = ds.RasterYSize
    band = ds.GetRasterBand(1)
    datatype = band.DataType
    arr = band.ReadAsArray(0, 0, size_x, size_y).astype(np.dtype(str_datatype))
    nodata = band.GetNoDataValue()

    rv = {'infile': infile,
          'array': arr,
          'size_x': size_x,
          'size_y': size_y,
          'nodata': nodata,
          'datatype': datatype
          }

    # Not sure if this function will cause a memory leak
    ds = None
    band = None
    arr = None

    return rv


def extent_args(extent):
    """Convert *extent tuple* to  *projwin* used in gdal command line utilities
    extent tuple format    : (xmin, ymin, xmax, ymax) i.e. min values, max values
    projwin argument order : (xmin, ymax, xmax, ymin) i.e. upper left, lower right"""

    return ['-projwin', str(extent[0]), str(extent[3]), str(extent[2]), str(extent[1]), '-projwin_srs', 'EPSG:5070']


def fill_nodata_values(infile, outfile, max_distance=35):
    '''Interpolate over NoData values with max distance of <max_distance>.'''
    # Fill values are basin specific
    #     To remove all no-data in the RedRiver zz, max_distance = 16
    #     To remove all no-data in the 'us' raster, max_distance = 31+
    # Command example: gdal_fillnodata.py -md 16 20110215_nodata.tif 20110215_fill16.tif

    # NOTE: The command "gdal_fillnodata.py" writes a temporary "Y index work file"
    #       in the current directory it was called from.  This will cause the command to fail
    #       if you do not have write permissions in "./"
    #       Change the working directory to the directory the output file will be written to
    os.chdir(os.path.abspath(os.path.dirname(outfile)))

    cmd = ['gdal_fillnodata.py', '-md', str(max_distance), infile, outfile]
    logging.debug(cmd)

    result = subprocess.check_call(cmd)
    logging.debug(result)

    return outfile


def get_without_vsicurl(url, outfile):
    """Helpful if vsicurl is not working for some reason.

    I ran into this issue trying to use gdal_translate /vsicurl/ from inside a container
    """

    outfile = os.path.abspath(outfile)

    cmd = ['curl', '-o', outfile, url]
    cmd = [str(c) for c in cmd]

    logging.debug('run command: {}'.format(' '.join(cmd)))

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    out, err = p.communicate()
    logging.debug('SubprocessResults: {}'.format(out))

    return outfile


def set_value_to_nodata(infile, outfile, value):
    '''Set pixels in <infile> with <value> to NoData. Save result to <outfile>'''

    # Command example: gdal_edit.py -a_nodata -9999 zz_ssmv11034tS__T0001TTNATS2011021505HP001.bil
    cmd = ['gdal_translate', '-a_nodata', value, '-co', 'compress=lzw', infile, outfile]
    logging.debug(cmd)

    result = subprocess.check_call(cmd)
    logging.debug(result)

    return outfile


def scale_raster_values(factor, infile, outfile):
    """Developed as a versatile way to do conversions like millimeters to meters"""

    # infile as a dataset
    ds = gdal.Open(infile, gdal.GA_ReadOnly)
    xsize = ds.RasterXSize
    ysize = ds.RasterYSize
    geotransform = ds.GetGeoTransform()
    projection = ds.GetProjection()

    # infile band
    band = ds.GetRasterBand(1)
    nodata_value = band.GetNoDataValue()

    # infile array
    array = band.ReadAsArray(0, 0, xsize, ysize).astype(np.dtype('float32'))

    # scaled_array
    scaled_array = np.where(array == nodata_value, nodata_value, array * factor)

    # write scaled array to raster
    scaled_raster = write_array_to_raster(
        scaled_array, outfile, xsize, ysize, geotransform, projection, gdal.GDT_Float32, nodata_value
    )

    ds = None
    xsize = None
    ysize = None
    geotransform = None
    projection = None
    band = None
    nodata_value = None
    array = None
    scaled_array = None

    return scaled_raster


def translate_url_to_vrt(url, outfile, projwin_args):

    logging.info(f'translate_url_to_vrt;\n  infile: {url};\n  outfile: {outfile}')

    cmd = ['gdal_translate', ] + extent_args(projwin_args) + [f'/vsicurl/{url}', outfile, ]

    cmd = [str(c) for c in cmd]

    logging.debug('run command: {}'.format(' '.join(cmd)))

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    out, err = p.communicate()
    logging.debug('SubprocessResults: {}'.format(out))

    return outfile


def create_overviews(infile, algorithm='average', levels=[2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]):

    logging.info('gdaladdo; infile: {}'.format(infile))

    cmd = ['gdaladdo', '-r', algorithm, infile] + [str(e) for e in levels]

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    out, err = p.communicate()

    return infile


def interpolate(infile, outfile, max_distance, nodata):

    with tempfile.TemporaryDirectory(prefix=uuid4().__str__()) as td:

        # This file will be automatically deleted
        _nodata = set_value_to_nodata(
            infile,
            os.path.join(td, f'_nodata.tif'),
            nodata
        )

        _filled = fill_nodata_values(
            _nodata,
            os.path.abspath(outfile),
            max_distance=max_distance
        )

    return _filled


def translate(infile, outfile, extra_args=None):
    """
    Convert SNODAS file to geotiff format
    """

    logging.info('gdal_translate; infile: {}; outfile: {}'.format(infile, outfile))

    # Basics of creating a tiled and compressed geotiff
    cmd = [
        'gdal_translate',
        '-of', 'GTiff',
        '-co', 'TILED=YES',
        '-co', 'COPY_SRC_OVERVIEWS=YES',
        '-co', 'COMPRESS=DEFLATE'
    ]

    if extra_args is not None:
        cmd += extra_args

    cmd += [infile, outfile]

    logging.debug('run command: {}'.format(' '.join(cmd)))

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    out, err = p.communicate()

    return outfile


def warp(infile, outfile, extra_args=[]):
    """Subprocess wrapper for calling gdalwarp"""

    logging.info('gdalwarp; infile: {}; outfile: {}'.format(infile, outfile))

    # Basics of creating a tiled and compressed geotiff
    cmd = ['gdalwarp', ] + extra_args + [infile, outfile, ]

    # Convert everything to a string
    cmd = [str(_c) for _c in cmd]

    logging.info('run command: {}'.format(' '.join(cmd)))

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    out, err = p.communicate()

    if not os.path.isfile(outfile):
        logging.fatal(f'Warp failed; file not created: {outfile}')

    return outfile
