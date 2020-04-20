#!/usr/env python3

import json
import logging
import os
import requests

from django.core.files import File

from handyutils.core import checksum

from products.models import (
    Product, ProductFile
)


def cumulus_product_from_productname(productname):

    ids = {
        'coldcontent': 'c2f2f0ed-d120-478a-b38f-427e91ab18e2',
        'snowdepth': 'e0baa220-1310-445b-816b-6887465cc94b',
        'swe': '757c809c-dda0-412b-9831-cb9bd0f62d1d',
        'snowmelt': '86526298-78fa-4307-9276-a7c0a0537d15',
        'snowpack_average_temperature': '57da96dc-fc5e-428c-9318-19f095f461eb',
        # Interpolated Products - Specifically 16 Cell Interpolation
        'nohrsc_snodas_swe_interpolated': '517369a5-7fe3-4b0a-9ef6-10f26f327b26',
        'nohrsc_snodas_snowpack_avg_temperature_interpolated': 'e97fbc56-ebe2-4d5a-bcd4-4bf3744d8a1b',
        'nohrsc_snodas_snowmelt_interpolated': '10011d9c-04a4-454d-88a0-fb7ba0d64d37',
        'nohrsc_snodas_snowdepth_interpolated': '2274baae-1dcf-4c4c-92bb-e8a640debee0',
        'nohrsc_snodas_coldcontent_interpolated': '33407c74-cdc2-4ab2-bd9a-3dff99ea02e4',
    }

    return ids[productname]


def save_to_cumulus_api(productname, productfile, productfile_datetime, verify=False, api_token=None):
            # If api_token is None, pull token from environment variables
    if api_token is None:
        api_token = os.environ['API_TOKEN']

    # Get API_URL and API_TOKEN from Environment Variables
    url = os.environ['API_URL'] + 'product/{}/files/'.format(cumulus_product_from_productname(productname))

    with open(productfile, 'rb') as f:

        r = requests.post(
            url,
            headers={
                'Authorization': 'Token {}'.format(api_token),
            },
            files={'file': f},
            data={
                'md5': checksum(productfile, algorithm='md5'),
                'product': cumulus_product_from_productname(productname),
                'datetime': productfile_datetime,
            },
            verify=verify
        )

    if not r.ok:
        msg = f'POST failed for: {url}; {productfile} with status: {r.status_code}'
        logging.critical(msg)
        raise Exception(msg)

    return r.json()


def save_to_cumulus_orm(productname, productfile, productfile_datetime):
    '''Save a Productfile using the Django ORM'''

    with open(productfile, 'rb') as f:

        product = Product.objects.get(pk=cumulus_product_from_productname(productname))

        pf = ProductFile()
        pf.product = product
        pf.file = File(f)
        pf.file.name = 'products/{}/{}'.format(product.name, productfile.split('/')[-1])
        pf.md5 = checksum(productfile, algorithm='md5')
        pf.datetime = productfile_datetime
        pf.save()


def post_to_cumulus(productname, productfile, productfile_datetime, verify=False, api_token=None, save_method='api'):

    if save_method == 'api':
        save_to_cumulus_api(productname, productfile, productfile_datetime, verify, api_token)

    if save_method == 'orm':
        save_to_cumulus_orm(productname, productfile, productfile_datetime)
