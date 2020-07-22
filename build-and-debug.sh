#!/bin/bash

VERSION=$(cat VERSION)

# Build GDAL Base Container
docker build . -t rsgis/geolambda:${VERSION}
docker run --rm -v $PWD:/home/geolambda -it rsgis/geolambda:${VERSION} package.sh

# Use GDAL Base Container to Build
# Container with Python Layer and Dependencies
cd python
docker build . --build-arg VERSION=${VERSION} -t rsgis/geolambda:${VERSION}-python
docker run --rm -v ${PWD}:/home/geolambda -t rsgis/geolambda:${VERSION}-python package-python.sh

cd ..

#
docker run \
    --rm \
    --name lambda_test \
    -v ${PWD}:/var/task \
    -v ${PWD}/lambda:/opt \
    -v ${PWD}/tmp:/tmp \
    -it \
    -e GDAL_DATA=/lambda/share/gdal \
    -e PROJ_LIB=/lambda/share/proj \
    -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID_CUMULUS_READER} \
    -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY_CUMULUS_READER} \
    -e CUMULUS_DBHOST=cumulusdb \
    -e CUMULUS_DBNAME=postgres \
    -e CUMULUS_DBPASS=postgres \
    -e CUMULUS_DBUSER=postgres \
    -e CUMULUS_MOCK_S3_UPLOAD=True \
    --network="container:database_cumulusdb_1" \
    lambci/lambda:build-python3.7 bash

