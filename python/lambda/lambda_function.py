import boto3
import botocore
import importlib
import os
import tempfile
import logging
import json

# set up logger
logger = logging.getLogger()
logger.setLevel(logging.WARNING)
# commented out to avoid duplicate logs in lambda
# logger.addHandler(logging.StreamHandler())

# imported to test loading of libraries
# from osgeo import gdal
# import pyproj
# import rasterio
# import shapely

from urllib.parse import unquote_plus

WRITE_TO_BUCKET = 'corpsmap-data'

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


def get_infile_processor(name):
    """Import library for processing a given filetype"""
    
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
    except ClientError as e:
        logging.error(e)
        return False
    return True


def write_entry_to_database(fileinfo):
    
    logging.debug(f'Write to Database Not Implemented: {fileinfo["file"]}')
    
    return True


def lambda_handler(event, context=None):
    """ Lambda handler """

    for record in event['Records']:

        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        
        logger.info(f'Lambda triggered by Bucket {bucket}; Key {key}')

        # # Filename and filetype
        pathparts = key.split('/')
        filetype, filename = pathparts[1], pathparts[-1]
        logger.info(f'Process filetype: {filetype}; file: {filename}')

        # Find library to unleash on file
        processor = get_infile_processor(filetype)
        logger.info(f'Using processor: {processor}')
       
        with tempfile.TemporaryDirectory() as td:
            
            _file = get_infile(bucket, key, os.path.join(td, filename))
            # Process the file and return a list of files
            outfiles = processor.process(_file, td)
            
            for _f in outfiles:
                # Write output files to different bucket
                write_key = 'cumulus/{}/{}'.format(_f["filetype"], _f["file"].split("/")[-1])
                upload_success = upload_file(
                    _f["file"], WRITE_TO_BUCKET, write_key
                )
                # Write Productfile Entry to Database
                if upload_success:
                    write_entry_to_database(_f)
            
        return outfiles
