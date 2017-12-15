#!/bin/bash

MY_DIR=`dirname "$(readlink -f "$0")"`
echo $MY_DIR
cd $MY_DIR
cd ../tdiff_path/

python ./total_path.py '201710 Prince George' /home/shared/Sync/Sites/Prince_George/Trips/2017/site_data/Data_Analysis/ delay-times.json pgr_total_path.json

python ./total_path.py '201607 Clyde River' /home/shared/Sync/Sites/Clyde_River/Trips/2016/Data_Analysis/ delay-times.json cly_total_path.json

python ./total_path.py '201708 Inuvik' /home/shared/Sync/Sites/Inuvik/Trips/2017/Data_Analysis/ delay-times.json inv_total_path.json

python ./total_path.py '201607 Rankin Inlet' /home/shared/Sync/Sites/Rankin_Inlet/Trips/2016/Data_Analysis/ delay-times.json rkn_total_path.json

python ./total_path.py '201706 Saskatoon' /home/shared/Sync/Sites/Saskatoon/SITE-VISITS-2017/Data_Analysis/ delay-times.json sas_total_path.json
