#!/bin/bash

MY_DIR=`dirname "$(readlink -f "$0")"`
echo $MY_DIR
cd $MY_DIR
cd ../

python ./compare_reflection.py Saskatoon /home/shared/Sync/Sites/Saskatoon/SITE-VISITS-2017/DATA/20171212/ /home/shared/Sync/Sites/Saskatoon/SITE-VISITS-2017/Data_Analysis/2009-antenna-comparison/ 2009-before-data.csv 2009-after-data.csv after-files.json
