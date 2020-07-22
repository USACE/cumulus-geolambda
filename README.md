# Cumulus-GeoLambda: Meteorologic Gridded Data Processing

## Summary

Dockerized geospatial dependencies for local development and creating custom AWS Lambda Layers.

This repository is a fork with modifications from [Developmentseed Geolambda](https://github.com/developmentseed/geolambda). Customizing the original image is a practice encouraged by the original repository writer(s) when you need a certain degree of customization. Additional information can be found in the readme of that project.

The information in this README.md focuses on the basics to get up and running and the differences introduced post-fork.

## CWBI Environment Setup

If you're using this project to develop meteorologic data processing workflows for the Civil Works Business Intelligence (CWBI) Amazon Web Services (AWS) environment, you'll need two environment variables set in your .bash_profile or equivalent. This allows `READ` access to S3 buckets for downloading sample data. The environment variables are:

- AWS_ACCESS_KEY_ID_CUMULUS_READER=<AWS_ACCESS_KEY_ID>
- AWS_SECRET_ACCESS_KEY_CUMULUS_READER=<AWS_SECRET_ACCESS_KEY>

## Local Development and Running Tests

Run the file [build-and-test.sh](build-and-test.sh). This re-builds docker containers and runs sample [AWS S3 Events](https://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html).

For the purpose of this project, an AWS S3 Event can be thought of as the the JSON that is produced when a file is uploaded, deleted, modified, etc. in a given S3 Bucket. AWS Lambda functions can configured to watch a S3 Bucket (or other AWS service offering) and execute their code whenever an event (or specific kind of event) takes place.

For this project, that means a Lambda function will process a Meteorologic Gridded Data file whenever a new file is uploaded to the S3 bucket.

JSON to simulate S3 events is located in the [mock_events](mock_events) directory.

The AWS Lambda environment is simulated using a [lambci/docker-lambda](https://github.com/lambci/docker-lambda) Docker image.

## Running as an AWS Lambda Function

### Lambda Layers

The files `rsgis-cumulus-geolambda-base.zip` and `rsgis-cumulus-geolambda-python.zip` are created by running the script [build.sh](build.sh). These are contain the geospatial dependencies that are made available in the Lambda runtime using [AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html). Use these two files to create two separate Lambda Layers compatible with Python 3.7 runtime environment, `rsgis-cumulus-geolambda-base` and `rsgis-cumulus-geolambda-python`. Add both layers to the Lambda function.

### Environment Variables

The following Environment Variables are required. All environment variables are prefixed with `CUMULUS_`

| Environment Variable   | Description                                                                      |
| ---------------------- | -------------------------------------------------------------------------------- |
| CUMULUS_DBHOST         | Database Host                                                                    |
| CUMULUS_DBNAME         | Database Name                                                                    |
| CUMULUS_DBPASS         | Database Password                                                                |
| CUMULUS_DBUSER         | Database User                                                                    |
| GDAL_DATA              | /opt/share/gdal (required for GDAL dependencies to work correctly)               |
| PROJ_LIB               | /opt/share/proj (required for GDAL dependencies to work correctly)               |
| CUMULUS_MOCK_S3_UPLOAD | FALSE (Useful for local testing; Mocks a successful S3 upload of processed files |

### Roles/Permissions

### S3 Bucket Configuration and S3 Lambda Trigger

The typical use case for this lambda function is to run the function against an input file as it is `Created` in an S3 Bucket. For the purpose of this explanation, let's assume we are using two S3 Buckets:

1. S3 Bucket `data-incoming` with target files to be processed located in the `/cumulus` sub-directory
2. S3 Bucket `data` with output files saved to the `/cumulus` sub-directory

Files to be processed by `cumulus-geolambda` are saved in bucket `data-incoming`. This triggers a `ObjectCreated` event. The Lambda function is configured to run whenever an `ObjectCreated` event occurs in the trigger location. Output files are saved in the bucket `data`.

NOTE: Using multiple buckets helps reduce (but not eliminate) the risk of infinite loops. For more information, do an internet search for "Lambda Infinite Loop Cost" or see the AWS recommendations [here](https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html).

To allow file uploads to S3 Bucket `data-incoming` to invoke the lambda function:

1.  In the Lambda Designer (or Infrastructure as Code solution), add an S3 Trigger.
2.  Configure the Trigger. For the example use case above, configuration fields would be:

| Field          | Value                    |
| -------------- | ------------------------ |
| Bucket         | `data-incoming`          |
| Event type     | All object create events |
| Prefix         | `cumulus/`               |
| Enable trigger | X                        |

To allow the lambda function to READ files from S3 Bucket `data-incoming` and WRITE files to S3 Bucket `data`, use a Lambda execution role with policies that include something similar to the following.

Note: Additional permissions may be required to allow things like VPC access, writing to cloudwatch, etc. These are typically covered in roles like `AWSLambdaBasicExeutionRole` or `AWSLambdaVPCAccessExecutionRole` that can be created ast part of initial Lambda function setup or added via additional IAM policies.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::data-incoming/*",
                "arn:aws:s3:::data-incoming"
            ]
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::data/cumulus/*"
        }
    ]
}
```

# @TODO Expand README.md
