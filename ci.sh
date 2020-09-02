#!/bin/bash

VERSION=$(cat VERSION)

# Build GDAL Base Container
docker build . -t rsgis/geolambda:${VERSION}
docker run --rm \
    -v ${GITHUB_WORKSPACE}:/home/geolambda \
    -it rsgis/geolambda:${VERSION} package.sh

# Upload to S3
aws s3 cp ${GITHUB_WORKSPACE}/corpsmap-cumulus-geolambda-base.zip \
          s3://corpsmap-lambda-zips/corpsmap-cumulus-geolambda-base.zip

# Use GDAL Base Container to Build
# Container with Python Layer and Dependencies
docker build python --build-arg VERSION=${VERSION} -t rsgis/geolambda:${VERSION}-python
docker run --rm \
    -v ${GITHUB_WORKSPACE}/python:/home/geolambda \
    -it rsgis/geolambda:${VERSION}-python package-python.sh

# Upload to S3
aws s3 cp ${GITHUB_WORKSPACE}/python/corpsmap-cumulus-geolambda-python.zip \
          s3://corpsmap-lambda-zips/corpsmap-cumulus-geolambda-python.zip
