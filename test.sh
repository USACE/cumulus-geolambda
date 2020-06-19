#!/bin/bash

docker run --rm \
    -v ${PWD}/lambda:/var/task \
    -v ${PWD}/../lambda:/opt \
    -e GDAL_DATA=/opt/share/gdal \
    -e PROJ_LIB=/opt/share/proj \
    -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID_CUMULUS_READER} \
    -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY_CUMULUS_READER} \
    -e CUMULUS_DBHOST=postgres \
    -e CUMULUS_DBNAME=postgres \
    -e CUMULUS_DBPASS=postgres \
    -e CUMULUS_DBUSER=postgres \
    --network="container:database_postgres_1" \
    lambci/lambda:python3.7 lambda_function.lambda_handler "$(cat $1)"