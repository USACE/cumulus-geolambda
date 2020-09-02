#!/bin/bash

# directory used for deployment
export DEPLOY_DIR=lambda

echo Creating deploy package

# make deployment directory and add lambda handler
mkdir -p $DEPLOY_DIR/lib

# copy libs
cp -P ${PREFIX}/lib/*.so* $DEPLOY_DIR/lib/
cp -P ${PREFIX}/lib64/libjpeg*.so* $DEPLOY_DIR/lib/

strip $DEPLOY_DIR/lib/* || true

# copy GDAL_DATA files over
echo "CHECKING RSYNC"
echo $(which rsync)
mkdir -p $DEPLOY_DIR/share
rsync -ax $PREFIX/share/gdal $DEPLOY_DIR/share/
rsync -ax $PREFIX/share/proj $DEPLOY_DIR/share/

# copy gdal binaries
# https://github.com/developmentseed/geolambda/issues/69
mkdir -p $DEPLOY_DIR/bin
cp $PREFIX/bin/gdaladdo $DEPLOY_DIR/bin/
cp $PREFIX/bin/gdalinfo $DEPLOY_DIR/bin/
cp $PREFIX/bin/gdal_translate $DEPLOY_DIR/bin/
cp $PREFIX/bin/gdalwarp $DEPLOY_DIR/bin/

# zip up deploy package
cd $DEPLOY_DIR
zip -ruq ../corpsmap-cumulus-geolambda-base.zip ./
