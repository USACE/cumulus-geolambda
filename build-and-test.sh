#!/bin/bash

VERSION=$(cat VERSION)

docker build . -t rsgis/geolambda:${VERSION}
docker run --rm -v $PWD:/home/geolambda -it rsgis/geolambda:${VERSION} package.sh

cd python
docker build . --build-arg VERSION=${VERSION} -t rsgis/geolambda:${VERSION}-python
docker run -v ${PWD}:/home/geolambda -t rsgis/geolambda:${VERSION}-python package-python.sh

docker run --rm -v ${PWD}/lambda:/var/task -v ${PWD}/../lambda:/opt \
           -e GDAL_DATA=/opt/share/gdal -e PROJ_LIB=/opt/share/proj \
           lambci/lambda:python3.7 lambda_function.lambda_handler '{}'
