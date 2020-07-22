#!/bin/bash

VERSION=$(cat VERSION)

# Build GDAL Base Container
docker build . -t rsgis/geolambda:${VERSION}
docker run -v ${GITHUB_WORKSPACE}:/home/geolambda \
    -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    -e AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} \
    -t rsgis/geolambda:${VERSION} package.sh

# Upload to S3
aws s3 cp ${GITHUB_WORKSPACE}/corpsmap-cumulus-geolambda-base.zip \
          s3://corpsmap-lambda-zips/corpsmap-cumulus-geolambda-base.zip

# Use GDAL Base Container to Build
# Container with Python Layer and Dependencies
docker build python --build-arg VERSION=${VERSION} -t rsgis/geolambda:${VERSION}-python
docker run -v ${GITHUB_WORKSPACE}/python:/home/geolambda \
    -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    -e AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} \
    -t rsgis/geolambda:${VERSION}-python package-python.sh

# Upload to S3
aws s3 cp ${GITHUB_WORKSPACE}/python/corpsmap-cumulus-geolambda-python.zip \
          s3://corpsmap-lambda-zips/corpsmap-cumulus-geolambda-python.zip
