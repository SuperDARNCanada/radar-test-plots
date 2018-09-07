#!/bin/bash
#
# To resolve issues with unicode chars in csv files
# when parsing; convert all to ascii or remove
# Mainly the degree symbol is a problem
# 08/23/2018 
# Marci Detwiller



DIRECTORY=$1
cd $DIRECTORY
cd ..
PARENT_DIR=$(pwd)
NO_UNICODE_DIRECTORY="${PARENT_DIR}/Data-wo-UTF8"
if [ ! -d "$NO_UNICODE_DIRECTORY" ]; then
    mkdir Data-wo-UTF8
fi
cd $DIRECTORY

for file in $(ls *.csv)
do
    outputfile="${NO_UNICODE_DIRECTORY}/$file"
    if [ ! -f $outputfile ]; then
        echo "${file} >> ${outputfile}"
        iconv -c -f utf-8 -t ascii $file >> $outputfile
    fi
done
