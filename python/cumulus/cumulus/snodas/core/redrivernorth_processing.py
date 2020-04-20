#!/usr/env python3
import django; django.setup()

from datetime import datetime, timedelta
import argparse
import os
from pytz import utc
import tempfile

from offices.models import Basin
from products.models import Product, ProductFile
from snodas.core.process import (
    cog_arguments,
    create_overviews,
    translate,
)
from snodas.core.interpolated_products import create_interpolated_swe
from geoprocess.core.base import translate_url_to_vrt
from .cumulus_integration import post_to_cumulus


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--start', required=True, help="Date to start file checks in YYYYMMDD")
    parser.add_argument('--end', required=True, help="Date to end file checks in YYYYMMDD")
    args = parser.parse_args()

    MASKRASTER = os.path.join(
        os.path.dirname(__file__), "no_data_areas_swe_20140201.tif"
    )

    # Set Start Time
    dtstart = datetime.strptime(args.start, '%Y%m%d-%H%M').replace(tzinfo=utc)
    # Set End Time
    dtend = datetime.strptime(args.end, '%Y%m%d-%H%M').replace(tzinfo=utc)

    dtimes = []
    while dtstart < dtend:
        dtimes.append(dtstart)
        dtstart += timedelta(days=1)

    [print(dt) for dt in dtimes]

    # Get the basin to work with
    basin = Basin.objects.get(pk="ad30f178-afc3-43b9-ba92-7bd139581217")

    # Get SWE files to process based on start time and end time
    swe_productfile_subset = ProductFile.objects.filter(datetime__gte=dtstart).filter(datetime__lte=dtend)
    # Don't query the database a bazillion times, handle the iteration in python
    swe_productfiles = {_s.datetime: _s for _s in swe_productfile_subset}

    for _pf_datetime, _pf in swe_productfiles.items():

        with tempfile.TemporaryDirectory() as td:
            # Get the file for processing local
            swefile = translate_url_to_vrt(
                _pf.file,
                os.path.abspath(
                    os.path.join(td, f'snodas_swe_{_pf["id"]}.vrt')
                ),
                (basin["x_min"], basin["y_min"], basin["x_max"], basin["y_max"],),
                projwin_srs="EPSG:5070"
            )

            # process the file
            outfile_basename = f'redrivernorth_swe_interpolated_{_pf_datetime.strftime("%Y%m%d")}'
            _interpolated_swe = create_interpolated_swe(
                _pf,
                _pf_datetime,
                MASKRASTER,
                os.path.abspath(
                    os.path.join(
                        td,
                        f'{outfile_basename}_tif.tif'
                    )
                )
            )

            # Overviews
            create_overviews(_interpolated_swe)

            # Translate to COG
            outfile_cog = translate(_interpolated_swe, f'{outfile_basename}_cog.tif', extra_args=cog_arguments())

            # save the file
            post_to_cumulus(
                'nohrsc_snodas_swe_interpolated',
                outfile_cog,
                verify=False,
                save_method='orm'
            )
