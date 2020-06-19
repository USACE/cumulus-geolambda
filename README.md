# Cumulus-GeoLambda: Meteorologic Gridded Data Processing

## Summary

Dockerized geospatial dependencies for local development and creating custom AWS Lambda Layers.

This repository is a fork with modifications from [Developmentseed Geolambda](https://github.com/developmentseed/geolambda). Customizing the original image is a practice encouraged by the original repository writer(s) when you need a certain degree of customization.  Additional information can be found in the readme of that project.

The information in this README.md focuses on the basics to get up and running and the differences introduced post-fork.

## CWBI Environment Setup

If you're using this project to develop meteorologic data processing workflows for the Civil Works Business Intelligence (CWBI) Amazon Web Services (AWS) environment, you'll need two environment variables set in your .bash_profile or equivalent.  This allows `READ` access to S3 buckets for downloading sample data.  The environment variables are:

* AWS_ACCESS_KEY_ID_CUMULUS_READER=<AWS_ACCESS_KEY_ID>
* AWS_SECRET_ACCESS_KEY_CUMULUS_READER=<AWS_SECRET_ACCESS_KEY>

## Local Development and Running Tests

Run the file [build-and-test.sh](build-and-test.sh). This re-builds docker containers and runs sample [AWS S3 Events](https://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html).

For the purpose of this project, an AWS S3 Event can be thought of as the the JSON that is produced when a file is uploaded, deleted, modified, etc. in a given S3 Bucket.  AWS Lambda functions can configured to watch a S3 Bucket (or other AWS service offering) and execute their code whenever an event (or specific kind of event) takes place.

For this project, that means a Lambda function will process a Meteorologic Gridded Data file whenever a new file is uploaded to the S3 bucket.

JSON to simulate S3 events is located in the [mock_events](mock_events) directory.

The AWS Lambda environment is simulated using a [lambci/docker-lambda](https://github.com/lambci/docker-lambda) Docker image.  

# @TODO Expand README.md