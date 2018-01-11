#!/bin/bash

MY_DIR=`dirname "$(readlink -f "$0")"`
echo $MY_DIR
cd $MY_DIR
cd ../tdiff_path/

# total_path_tdiff

python ./total_path_tdiff.py '201710 Prince George' /home/shared/Sync/Sites/Prince_George/Trips/2017/site_data/Data_Analysis/ delay-times.txt pgr_total_path.txt

python ./total_path_tdiff.py '201607 Clyde River' /home/shared/Sync/Sites/Clyde_River/Trips/2016/Data_Analysis/ delay-times.txt cly_total_path.txt

python ./total_path_tdiff.py '201708 Inuvik' /home/shared/Sync/Sites/Inuvik/Trips/2017/Data_Analysis/ delay-times.txt inv_total_path.txt

python ./total_path_tdiff.py '201607 Rankin Inlet' /home/shared/Sync/Sites/Rankin_Inlet/Trips/2016/Data_Analysis/ delay-times.txt rkn_total_path.txt

python ./total_path_tdiff.py '201706 Saskatoon' /home/shared/Sync/Sites/Saskatoon/SITE-VISITS-2017/Data_Analysis/ delay-times.txt sas_total_path.txt

# total_path_arrays

python ./total_path_arrays.py '201710 Prince George' /home/shared/Sync/Sites/Prince_George/Trips/2017/site_data/Data_Analysis/

python ./total_path_arrays.py '201607 Clyde River' /home/shared/Sync/Sites/Clyde_River/Trips/2016/Data_Analysis/

python ./total_path_arrays.py '201708 Inuvik' /home/shared/Sync/Sites/Inuvik/Trips/2017/Data_Analysis/

python ./total_path_arrays.py '201607 Rankin Inlet' /home/shared/Sync/Sites/Rankin_Inlet/Trips/2016/Data_Analysis/

python ./total_path_arrays.py '201706 Saskatoon' /home/shared/Sync/Sites/Saskatoon/SITE-VISITS-2017/Data_Analysis/