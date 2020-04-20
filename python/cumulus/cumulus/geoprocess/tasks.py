from config import celery_app
from celery.utils.log import get_task_logger

import io
import os
import json
from tempfile import TemporaryDirectory

from django.conf import settings as SETTINGS
from django.core.files.base import ContentFile

from products.models import ProductFile, ProductFileStatistics
from .core.zstats import zstats_redriver, zstats_generic

# Logger for specific task
logger = get_task_logger(__name__)


@celery_app.task()
def task_statistics_redrivernorth_for_productfile(productfile_id):
    """This should be deprecated in lieu of task_statistics_for_productfile, which is more generic
    Review methods contained in .core.zstats and deprecate as possible
    """

    # Get Productfile
    _pf = ProductFile.objects.get(pk=str(productfile_id))
    # Compute zonal statistics
    _pfstats = zstats_redriver(f'{SETTINGS.MEDIA_URL}{_pf.file.name}')
    # Write zonal statistics to file
    _pfs = ProductFileStatistics(
        basin="redrivernorth",
        productfile=_pf,
    )
    # Attach JSON File
    _pfs.statistics = ContentFile(json.dumps(_pfstats, separators=(",", ":")).encode())
    _pfs.statistics.name = f'statistics__redrivernorth__{_pf.product.name}__{_pf.datetime.strftime("%Y%m%d-%H%M%S")}.json'
    # Save ProductFileStatistics
    _pfs.save()

    return {"created": _pfs.pk}


@celery_app.task()
def task_statistics_for_productfile(productfile_id, shapefile):
    _pf = ProductFile.objects.get(pk=str(productfile_id))
    # Compute zonal statistics
    _pfstats = zstats_generic(f'{SETTINGS.MEDIA_URL}{_pf.file.name}', shapefile)
    # Write zonal statistics to file
    _basin = os.path.splitext(os.path.basename(shapefile))[0]
    _pfs = ProductFileStatistics(
        basin=_basin,
        productfile=_pf,
    )
    # Attach JSON File
    _pfs.statistics = ContentFile(json.dumps(_pfstats, separators=(",", ":")).encode())
    _pfs.statistics.name = f'statistics__{_basin}__{_pf.product.name}__{_pf.datetime.strftime("%Y%m%d-%H%M%S")}.json'
    # Save ProductFileStatistics
    _pfs.save()

    return {"created": _pfs.pk}


@celery_app.task(task_reject_on_worker_lost=True, retry_kwargs={'max_retries': 3})
def process_and_post(datetime, infile_type, save_method='orm'):

    with TemporaryDirectory() as td:
        processed_files = process_snodas_for_date(datetime, infile_type, td)
        post_results = []
        for productname, productfile in processed_files['cog'].items():
            p = post_to_cumulus(productname, productfile, datetime, save_method=save_method)
            post_results.append(p)
