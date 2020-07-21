from datetime import datetime
import os
import re


from ..geoprocess.core.base import info, translate, create_overviews


def prism_datetime_from_filename(infile):
    """Helper function to return datetime from a prism-formatted filename
    Works on file absolute path, relative path, or simple filename
    """
    
    pattern = r"PRISM_[a-z]+_early_4kmD2_([0-9]+)_bil.zip"
    
    m = re.match(pattern, os.path.basename(infile))
    if m is not None:
        return datetime.strptime(m[1], '%Y%m%d')
    
    return None


def prism_convert_to_cog(infile, outdir):
    """Function to create the COG file
    """

    filename_no_extension = os.path.splitext(os.path.basename(infile))[0]

    # See vsidriver chaining: https://gdal.org/user/virtual_file_systems.html
    bilfile = f'/vsizip/{infile}/{filename_no_extension}.bil'
       
    # Create GeoTIFF
    translated = translate(
        bilfile,
        os.path.join(outdir, "translated.tif")
    )
    # Create Overviews
    create_overviews(translated)
    # COG
    outfile_cog = translate(
        translated,
        os.path.join(outdir, f"{filename_no_extension}_cloud_optimized.tif"),
    )

    return outfile_cog