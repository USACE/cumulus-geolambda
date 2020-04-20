#!/usr/bin/env python3
import django; django.setup()

import os

from offices.models import Basin


#from rasterstats import zonal_stats

# Inputs to functions
# Product
# Subscribed basins for product (or just all basins...)
# basin features --> project to SHG
# .tif projected to SHG

def get_raster():

    return(os.path.abspath('./GaugeCorr_QPE_01H_00.00_20190605-000000.grib2.gz'))


def get_vector(crs=None, ):
    """Returns iterable of python objects that support the __geo_interface__.
    Accepts an optional crs parameter.  If crs is provided, vectors will be projected
    to "crs".
    """

    # fetch basins shapes from database
    basins = Basin.objects.all()
    
    # unique identifiers (primary keys)
    _uids = [b.id for b in basins]
    
    # polygons
    _mpolys = []
    for b in basins:
        _mpolys.append(b.mpoly)

    # transform multipolygons in place if coordinate reference is specified
    if crs is not None:
        [m.transform(crs) for m in _mpolys]
    
    return (_uids, _mpolys)
    

if __name__ == '__main__':
    
    # get vectors, projected to "SHG" (EPSG 5070)
    v = get_vector(5070)

    # get raster, projected to "SHG" (EPSG 5070)
    r = get_raster()

    # ... to be continued ...
