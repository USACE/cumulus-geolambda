import boto3
import botocore
import botocore.exceptions
import importlib
import os
import tempfile
import logging
import json
import psycopg2
import psycopg2.extras
import shutil

# set up logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# commented out to avoid duplicate logs in lambda
logger.addHandler(logging.StreamHandler())

# imported to test loading of libraries
# from osgeo import gdal
# import pyproj
# import rasterio
# import shapely

from urllib.parse import unquote_plus

# Configuration
###################################
WRITE_TO_BUCKET = 'corpsmap-data'
# CUMULUS_MOCK_S3_UPLOAD
# (for testing without S3 Bucket Upload Access/Permission)
if os.getenv('CUMULUS_MOCK_S3_UPLOAD', default="False").upper() == "TRUE": 
    CUMULUS_MOCK_S3_UPLOAD = True
else:
    # If CUMULUS_MOCK_S3_UPLOAD environment variable is unset then CUMULUS_MOCK_S3_UPLOAD will equal False
    CUMULUS_MOCK_S3_UPLOAD = False
###################################

def get_infile(bucket, key, filepath):
    
    s3 = boto3.resource('s3')
    try:
        s3.Bucket(bucket).download_file(key, filepath)
        return os.path.abspath(filepath)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            logger.fatal(f'OBJECT DOES NOT EXIST: {key}')
            return None
        else:
            raise

def db_connection():
    user = os.getenv('CUMULUS_DBUSER')
    host = os.getenv('CUMULUS_DBHOST')
    dbname = os.getenv('CUMULUS_DBNAME')
    password = os.getenv('CUMULUS_DBPASS')
    
    return psycopg2.connect(
        user=user,
        host=host,
        dbname=dbname,
        password=password
    )

def get_infile_processor(name):
    """Import library for processing a given product_name"""
    
    processor = importlib.import_module(f'cumulus.processors.{name}')
    
    return processor


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    Copied from https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except botocore.exceptions.ClientError as e:
        logger.error(e)
        return False
    return True

def get_acquirables():
    '''list of acquirables in the database'''
    try:
        conn = db_connection()
        c = conn.cursor()
        c.execute("SELECT name from acquirable")
        rows = c.fetchall()

    finally:
        c.close()
        conn.close()
    
    return [r[0] for r in rows]


def get_products():
    '''Map of <name>:<product_id> for all products in the database'''
    
    try:
        conn = db_connection()
        c = conn.cursor()
        c.execute("SELECT name, id from product")
        rows = c.fetchall()
    finally:
        c.close()
        conn.close()
    
    return { r[0]: r[1] for r in rows}


def write_database(entries):
    
    def dict_to_tuple(d):
        return tuple([d['datetime'], d['file'], d['product_id']])
    
    values = [dict_to_tuple(e) for e in entries]

    try:
        conn = db_connection()
        c = conn.cursor()
        psycopg2.extras.execute_values(
            c, "INSERT INTO productfile (datetime, file, product_id) VALUES %s", values,
        )
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        c.close()
        conn.close()
    
    return len(entries)


def lambda_handler(event, context=None):
    """ Lambda handler """

    for record in event['Records']:

        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])

        logger.info(f'Lambda triggered by Bucket {bucket}; Key {key}')

        # # Filename and product_name
        pathparts = key.split('/')
        acquirable_name, filename = pathparts[1], pathparts[-1]
        logger.info(f'Process acquirable_name: {acquirable_name}; file: {filename}')

        # Check if acquirable is valid in the database
        acquirables = get_acquirables()
        logger.info(f'valid acquirables in database: {acquirables}')
        if acquirable_name not in acquirables:
            logger.error(f'acquirable_name not in database: {acquirable_name}')
            return []

        # Find library to unleash on file
        processor = get_infile_processor(acquirable_name)
        logger.info(f'Using processor: {processor}')
       
        with tempfile.TemporaryDirectory() as td:
            
            _file = get_infile(bucket, key, os.path.join(td, filename))
            # Process the file and return a list of files
            outfiles = processor.process(_file, td)
            logger.debug(f'outfiles: {outfiles}')
            
            # Keep track of successes to send as single database query at the end
            successes = []
            # Valid products in the database
            product_map = get_products()
            for _f in outfiles:
                # See that we have a valid 
                if _f["filetype"] in product_map.keys():
                    # Write output files to different bucket
                    write_key = 'cumulus/{}/{}'.format(_f["filetype"], _f["file"].split("/")[-1])
                    if CUMULUS_MOCK_S3_UPLOAD:
                        # Mock good upload to S3
                        upload_success = True
                        # Copy file to tmp directory on host
                        # shutil.copy2 will overwrite a file if it already exists.
                        shutil.copy2(_f["file"], "/tmp")
                    else:
                        upload_success = upload_file(
                            _f["file"], WRITE_TO_BUCKET, write_key
                        )
                    # Write Productfile Entry to Database
                    if upload_success:
                        successes.append({
                            "product_id": product_map[_f["filetype"]],
                            "datetime": _f['datetime'],
                            "file": write_key,
                        })
            
            count = write_database(successes)
            
        return {
            "count": count,
            "productfiles": successes
        }
