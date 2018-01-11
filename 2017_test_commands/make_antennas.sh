#!/bin/bash

MY_DIR=`dirname "$(readlink -f "$0")"`
echo $MY_DIR
cd $MY_DIR
cd ../tdiff_path/

python ./antennas.py Saskatoon /home/shared/Sync/Sites/Saskatoon/SITE-VISITS-2017/DATA/ /home/shared/Sync/Sites/Saskatoon/SITE-VISITS-2017/Data_Analysis/ANTENNAS-ALONE/ vswr-files.json phase-antennas.txt
