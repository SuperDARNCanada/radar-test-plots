#!/bin/bash

MY_DIR=`dirname "$(readlink -f "$0")"`
echo $MY_DIR
cd $MY_DIR
cd ../tdiff_path/

python ./transmitter_paths.py '20170930 Prince George' /home/shared/Sync/Sites/Prince_George/Trips/2017/site_data/DATA/ /home/shared/Sync/Sites/Prince_George/Trips/2017/site_data/Data_Analysis/Transmitter-Path/ path-files.json delay-times.json

python ./transmitter_paths.py '20160701 Clyde River' /home/shared/Sync/Sites/Clyde_River/Trips/2016/DATA/ /home/shared/Sync/Sites/Clyde_River/Trips/2016/Data_Analysis/Transmitter-Path/ path-files.json delay-times.json

python ./transmitter_paths.py '20170813 Inuvik' /home/shared/Sync/Sites/Inuvik/Trips/2017/DATA/ /home/shared/Sync/Sites/Inuvik/Trips/2017/Data_Analysis/Transmitter-Path/ path-files.json delay-times.json

python ./transmitter_paths.py '20160719 Rankin Inlet' /home/shared/Sync/Sites/Rankin_Inlet/Trips/2016/DATA/ /home/shared/Sync/Sites/Rankin_Inlet/Trips/2016/Data_Analysis/Transmitter-Path/ path-files.json delay-times.json

python ./transmitter_paths.py '20170630 Saskatoon' /home/shared/Sync/Sites/Saskatoon/SITE-VISITS-2017/DATA/ /home/shared/Sync/Sites/Saskatoon/SITE-VISITS-2017/Data_Analysis/Transmitter-Path/ path-files.json delay-times.json

