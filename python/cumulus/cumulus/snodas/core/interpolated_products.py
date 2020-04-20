#!/usr/env python3

import os

from uuid import uuid4
import logging
import tempfile

from geoprocess.core.base import (
    create_overviews,
    translate,
    interpolate,
)

from .lakefix import (
    file_needs_lakefix,
    lakefix_zero_values_to_nodata,
    lakefix_set_cells_to_nodata
)

from .process import snodas_write_coldcontent

from .helpers import snodas_get_nodata_value

MASKRASTER = os.path.abspath(
    os.path.join(
        "/app/cumulus/snodas/core",
        "no_data_areas_swe_20140201.tif"
    )
)


def create_interpolated_swe(swe, datetime, outfile, max_distance):

    with tempfile.TemporaryDirectory(prefix=uuid4().__str__()) as td:

        # Fix the zero values around lakes, a bug in SNODAS files from ~2014 to present (2019)
        if file_needs_lakefix(datetime, 1034):
            swe = lakefix_zero_values_to_nodata(
                swe,
                os.path.join(td, f'_lakefix.tif'),
                snodas_get_nodata_value(datetime),
                MASKRASTER
            )

        logging.debug(f'Raw Input: {swe}')

        _interpolated = interpolate(
            swe,
            os.path.join(td, '_interpolated.tif'),
            max_distance,
            snodas_get_nodata_value(datetime)
        )

        logging.debug(f'Interpolated SWE GTiff: {_interpolated}')

        # Overviews
        create_overviews(_interpolated)

        # Translate to COG
        _cog = translate(_interpolated, os.path.abspath(outfile))
        logging.debug(f'Interpolated COG: {_cog}')

    return _cog


def create_interpolated_snowdepth(snowdepth, datetime, outfile, max_distance):

    with tempfile.TemporaryDirectory(prefix=uuid4().__str__()) as td:

        # Fix the zero values around lakes, a bug in SNODAS files from ~2014 to present (2019)
        if file_needs_lakefix(datetime, 1034):
            snowdepth = lakefix_zero_values_to_nodata(
                snowdepth,
                os.path.join(td, f'_lakefix.tif'),
                snodas_get_nodata_value(datetime),
                MASKRASTER
            )

        logging.debug(f'Raw Input: {snowdepth}')

        _interpolated = interpolate(
            snowdepth,
            os.path.join(td, '_interpolated.tif'),
            max_distance,
            snodas_get_nodata_value(datetime)
        )

        logging.debug(f'Interpolated snowdepth GTiff: {_interpolated}')

        # Overviews
        create_overviews(_interpolated)

        # Translate to COG
        _cog = translate(_interpolated, os.path.abspath(outfile))
        logging.debug(f'Interpolated COG: {_cog}')

    return _cog


def create_interpolated_snowtemp(snowtemp, swe_interpolated, datetime, max_distance, outfile):

    with tempfile.TemporaryDirectory(prefix=uuid4().__str__()) as td:
    
        _interpolated = interpolate(
            snowtemp,
            os.path.join(td, '_interpolated.tif'),
            max_distance,
            snodas_get_nodata_value(datetime)
        )

        logging.debug(f'Interpolated snowtemp GTiff: {_interpolated}')

        # Return legitimate nodata cells back to nodata
        _interpolated_nodata = lakefix_set_cells_to_nodata(_interpolated, snowtemp, swe_interpolated,)

        # Overviews
        create_overviews(_interpolated_nodata)

        # Translate to COG
        _cog = translate(_interpolated_nodata, os.path.abspath(outfile))
        logging.debug(f'Interpolated COG: {_cog}')

    return _cog


def create_interpolated_snowmelt(snowmelt, swe_interpolated, datetime, max_distance, outfile):

    with tempfile.TemporaryDirectory(prefix=uuid4().__str__()) as td:
    
        _interpolated = interpolate(
            snowmelt,
            os.path.join(td, '_interpolated.tif'),
            max_distance,
            snodas_get_nodata_value(datetime)
        )

        logging.debug(f'Interpolated snowmelt GTiff: {_interpolated}')

        # Return legitimate nodata cells back to nodata
        _interpolated_nodata = lakefix_set_cells_to_nodata(_interpolated, snowmelt, swe_interpolated,)

        # Overviews
        create_overviews(_interpolated_nodata)

        # Translate to COG
        _cog = translate(_interpolated_nodata, os.path.abspath(outfile))
        logging.debug(f'Interpolated COG: {_cog}')

    return _cog


def create_interpolated_coldcontent(snowpack_average_temperature_interpolated, swe_interpolated, outfile):

    with tempfile.TemporaryDirectory(prefix=uuid4().__str__()) as td:
    
        _coldcontent = snodas_write_coldcontent(
            snowpack_average_temperature_interpolated,
            swe_interpolated,
            os.path.join(td, '_coldcontent.tif'),
        )

        logging.debug(f'Interpolated coldcontent GTiff: {_coldcontent}')

        # Overviews
        create_overviews(_coldcontent)

        # Translate to COG
        _cog = translate(_coldcontent, os.path.abspath(outfile))
        logging.debug(f'Interpolated COG: {_cog}')

    return _cog
