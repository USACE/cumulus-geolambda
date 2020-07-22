#!/bin/bash

VERSION=$(cat VERSION)

# Build GDAL Base Container
docker build . -t rsgis/geolambda:${VERSION}
docker run --rm -v $PWD:/home/geolambda -it rsgis/geolambda:${VERSION} package.sh

# Use GDAL Base Container to Build
# Container with Python Layer and Dependencies
cd python
docker build . --build-arg VERSION=${VERSION} -t rsgis/geolambda:${VERSION}-python
docker run -v ${PWD}:/home/geolambda -t rsgis/geolambda:${VERSION}-python package-python.sh
