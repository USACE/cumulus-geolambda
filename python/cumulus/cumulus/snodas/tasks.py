from config import celery_app
from django.conf import settings as SETTINGS

import logging
import os
from tempfile import TemporaryDirectory

from products.models import ProductFile
from geoprocess.core.base import get_without_vsicurl

from .core.process import process_snodas_for_date
from .core.interpolated_products import (
    create_interpolated_swe,
    create_interpolated_snowdepth,
    create_interpolated_snowtemp,
    create_interpolated_snowmelt,
    create_interpolated_coldcontent
)
from .core.cumulus_integration import post_to_cumulus

def process_and_post(datetime, infile_type, save_method='orm'):

    with TemporaryDirectory() as td:
        processed_files = process_snodas_for_date(datetime, infile_type, td)
        post_results = []
        for productname, productfile in processed_files['cog'].items():
            p = post_to_cumulus(productname, productfile, datetime, save_method=save_method)
            post_results.append(p)

    return post_results


@celery_app.task()
def interpolate_snodas_for_datetime(datetime, max_distance):
    """This should be broken up into smaller tasks and repeated code should be eliminated"""

    with TemporaryDirectory() as td:

        # Keep track of the files that are processed
        processed_productfiles = []

        # SWE
        # ---------------------------------------------------------------------------------------------------
        product_name = 'nohrsc_snodas_swe'
        try:
            _pf = ProductFile.objects.filter(product__name=product_name, datetime=datetime).get()
            logging.debug(f'Get file: {_pf.file.name}')
            swe = get_without_vsicurl(
                f'{SETTINGS.MEDIA_URL}{_pf.file.name}',
                os.path.join(
                    td,
                    f'{product_name}_{_pf.datetime.strftime("%Y%m%d")}.tif'
                ),
            )

            swe_interpolated = create_interpolated_swe(
                swe,
                _pf.datetime,
                os.path.join(
                    td, f'{product_name}_interpolated_{max_distance}_{_pf.datetime.strftime("%Y%m%d")}.tif'),
                max_distance
            )

            processed_productfiles.append(
                {"name": f'{product_name}_interpolated', "file": swe_interpolated, "datetime": _pf.datetime}
            )
        except:
            logging.critical(f'Could not process; {product_name} for date: {_pf.datetime.strftime("%Y%m%d")}')

        # SNOWDEPTH
        # ---------------------------------------------------------------------------------------------------
        product_name = 'nohrsc_snodas_snowdepth'
        try:
            _pf = ProductFile.objects.filter(product__name=product_name, datetime=datetime).get()
            snowdepth = get_without_vsicurl(
                f'{SETTINGS.MEDIA_URL}{_pf.file.name}',
                os.path.join(
                    td,
                    f'{product_name}_{_pf.datetime.strftime("%Y%m%d")}.tif'
                ),
            )

            snowdepth_interpolated = create_interpolated_snowdepth(
                snowdepth,
                _pf.datetime,
                os.path.join(
                    td, f'{product_name}_interpolated_{max_distance}_{_pf.datetime.strftime("%Y%m%d")}.tif'),
                max_distance
            )

            processed_productfiles.append(
                {"name": f'{product_name}_interpolated', "file": snowdepth_interpolated, "datetime": _pf.datetime}
            )
        except:
            logging.critical(f'Could not process; {product_name} for date: {_pf.datetime.strftime("%Y%m%d")}')

        # SNOWPACK AVERAGE TEMPERATURE
        # ---------------------------------------------------------------------------------------------------
        product_name = 'nohrsc_snodas_snowpack_avg_temperature'
        try:
            _pf = ProductFile.objects.filter(product__name=product_name, datetime=datetime).get()
            snowtemp = get_without_vsicurl(
                f'{SETTINGS.MEDIA_URL}{_pf.file.name}',
                os.path.join(
                    td,
                    f'{product_name}_{_pf.datetime.strftime("%Y%m%d")}.tif'
                ),
            )

            snowtemp_interpolated = create_interpolated_snowtemp(
                snowtemp,
                swe_interpolated,
                _pf.datetime,
                max_distance,
                os.path.join(
                    td, f'{product_name}_interpolated_{max_distance}_{_pf.datetime.strftime("%Y%m%d")}.tif')
            )

            processed_productfiles.append(
                {"name": f'{product_name}_interpolated', "file": snowtemp_interpolated, "datetime": _pf.datetime}
            )
        except:
            logging.critical(f'Could not process; {product_name} for date: {_pf.datetime.strftime("%Y%m%d")}')

        # SNOWMELT
        # ---------------------------------------------------------------------------------------------------
        product_name = 'nohrsc_snodas_snowmelt'
        try:
            _pf = ProductFile.objects.filter(product__name=product_name, datetime=datetime).get()
            snowmelt = get_without_vsicurl(
                f'{SETTINGS.MEDIA_URL}{_pf.file.name}',
                os.path.join(
                    td,
                    f'{product_name}_{_pf.datetime.strftime("%Y%m%d")}.tif'
                ),
            )

            snowmelt_interpolated = create_interpolated_snowmelt(
                snowmelt,
                swe_interpolated,
                _pf.datetime,
                max_distance,
                os.path.join(
                    td, f'{product_name}_interpolated_{max_distance}_{_pf.datetime.strftime("%Y%m%d")}.tif')
            )

            processed_productfiles.append(
                {"name": f'{product_name}_interpolated', "file": snowmelt_interpolated, "datetime": _pf.datetime}
            )

        except:
            logging.critical(f'Could not process; {product_name} for date: {_pf.datetime.strftime("%Y%m%d")}')

        # COLD CONTENT
        # ---------------------------------------------------------------------------------------------------
        product_name = 'nohrsc_snodas_coldcontent'
        try:
            coldcontent_interpolated = create_interpolated_coldcontent(
                snowtemp_interpolated,
                swe_interpolated,
                os.path.join(td, f'{product_name}_interpolated_{max_distance}_{datetime.strftime("%Y%m%d")}.tif')
            )

            processed_productfiles.append(
                {"name": f'{product_name}_interpolated', "file": coldcontent_interpolated, "datetime": datetime}
            )
        except:
            logging.critical(f'Could not process; {product_name} for date: {datetime.strftime("%Y%m%d")}')

        for _processed in processed_productfiles:

            logging.info(f'post to database: {_processed["name"]}; {_processed["file"]}')

            post_to_cumulus(
                f'{_processed["name"]}',
                _processed['file'],
                _processed['datetime'],
                verify=False,
                save_method='orm'
            )
