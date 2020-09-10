from tempfile import TemporaryDirectory
import os
import json
import requests
import boto3
import botocore
import botocore.exceptions

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

# event = {
#     "id": "233bf9b3-9ca6-497f-806a-9d198a28abdb",
#     "output_bucket": "corpsmap-data",
#     "key": "cumulus/downloads/dss/filename.dss",
#     "contents": [
#         {"name": "ncep_mrms_gaugecorr_qpe_01h", "dss_fpart": "NCEP-MRMS-QPE", "bucket": "corpsmap-data", "key": "cumulus/ncep_mrms_gaugecorr_qpe_01h/MRMS_GaugeCorr_QPE_01H_00.00_20200903-150000.tif"},
#         # {"name": "NCEP-rtma_airtemp", "dss_fpart": "NDGD-RTMA", "file": "S3://corpsmap-data/cumulus/ncep-rtma_airtemp/2020021005_cog.tif"},
#         # {"name": "NCEP-rtma_airtemp", "dss_fpart": "NDGD-RTMA", "file": "S3://corpsmap-data/cumulus/ncep-rtma_airtemp/2020021005_cog.tif"},
#         # {"name": "nohrsc_snodas_swe", "dss_fpart": "SNODAS", "file": "S3://corpsmap-data/cumulus/nohrsc_snodas_swe/zz_ssmv11034tS__T0001TTNATS2020021005HP001_cloud_optimized.tif"},
#         # {"name": "nohrsc_snodas_swe", "dss_fpart": "SNODAS", "file": "S3://corpsmap-data/cumulus/nohrsc_snodas_swe/zz_ssmv11034tS__T0001TTNATS2020021005HP001_cloud_optimized.tif"}
#     ]}

STATUS = {
    'FAILED': 'a553101e-8c51-4ddd-ac2e-b011ed54389b',
    'INITIATED': '94727878-7a50-41f8-99eb-a80eb82f737a',
    'SUCCESS': '3914f0bd-2290-42b1-bc24-41479b3a846f'
}

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


def lambda_handler(event, context=None):

    id, contents = event['id'], event['contents']
    filecount = len(contents)
    
    # Get product count from event contents
    with TemporaryDirectory() as td:
        print(f'Working in temporary directory: {td}')
        for idx in range(filecount):           
            
            # Filename and product_name
            pathparts = contents[idx]['key'].split('/')
            product_name, filename = pathparts[1], pathparts[-1]
            # logger.info(f'Process acquirable_name: {acquirable_name}; file: {filename}')
            

            # Download specified file
            _file = get_infile(contents[idx]['bucket'], contents[idx]['key'], os.path.join(td, filename))

            print(_file)
            print(os.path.getsize(_file))

            # requests.put(
            #     f'http://localhost:3030/cumulus/downloads/{id}',
            #     json = {
            #         "id"
            #         "status_id": STATUS['INITIATED'],
            #         "progress": int((idx+1 / filecount)*100)
            #     }
            # )
            print('-'*64)
                

        # Save file to specified S3 path
        # success = upload_file(_file, bucket, key)
        
    return json.dumps({
        "success": "SOMETHING",
    })

if __name__ == "__main__":
    lambda_handler(event)