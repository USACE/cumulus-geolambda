#!/usr/env python3

import django; django.setup()

import argparse
import logging
import math
import os
import subprocess
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.files import File

from offices.models import Basin
from products.models import ProductFile
from cumulus.utils.core.utils import checksum

from .base import translate, warp
from .helpers import buffered_extent, checksum

# WARNING: EPSG 5070 (SHG) Hard Coded Temporarily


def subgrids(productfile_object, mode='all'):
    
    if mode == 'all':
        # Get Envelope for Each Basin. Note: Basin.objects.all() is Django ORM
        # b.mpoly.envelope returns tuple with these values (xmin, ymin, xmax, ymax) 
        basin_envelopes = {b.id: {'envelope': b.mpoly.envelope, 'office_id': b.office_id}
            for b in Basin.objects.all()
        }

    # Transform Envelopes From Lat/Lon (EPSG ???) to SHG (EPSG 5070)
    [e['envelope'].transform(5070) for e in basin_envelopes.values()]

    # SHG Clip Extents For Each Basin; With Buffer (2*2000M; 4KM Buffer *Minimum*)
    buffered_basin_extents = {k: buffered_extent(v['envelope'].extent, 2, 2000) for k,v in basin_envelopes.items()}

    for uuid, extent in buffered_basin_extents.items():

        with open(NamedTemporaryFile(suffix='.tif').name, 'w+b') as f:
            # Write to Temporary File
            translate(productfile_object.file.path, f.name, extent)
            # Create ProductFile
            p = ProductFile()  # New ProductFile
            p.product = productfile_object.product  # Set FK of new product to parent product
            p.file = File(f)
            p.file.name = '{}_{}'.format('MRMS', uuid)
            p.md5 = checksum(f.name, algorithm='MD5')
            p.save()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, choices=['all', 'subscribed'])
    parser.add_argument('--product-id', type=str)
    args = parser.parse_args()

    product = Products.objects.get(id=args.product_id)
    
    subgrids(product, mode)


if __name__ == '__main__':
    main()

