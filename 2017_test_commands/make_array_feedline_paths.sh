#!/bin/bash

MY_DIR=`dirname "$(readlink -f "$0")"`
echo $MY_DIR
cd $MY_DIR
cd ../tdiff_path/

python ./array_feedline_paths.py '20171003 Prince George Post-Fix' /home/shared/Sync/Sites/Prince_George/Trips/2017/site_data/DATA/ /home/shared/Sync/Sites/Prince_George/Trips/2017/site_data/Data_Analysis/Feedline-Path/ vswr-files-post-work.json delay-times.json

python ./array_feedline_paths.py '20170930 Prince George Pre-Fix' /home/shared/Sync/Sites/Prince_George/Trips/2017/site_data/DATA/ /home/shared/Sync/Sites/Prince_George/Trips/2017/site_data/Data_Analysis/Feedline-Path/ vswr-files-pre-work.json None

python ./array_feedline_paths.py '20160628 Clyde River Pre-Fix' /home/shared/Sync/Sites/Clyde_River/Trips/2016/DATA/ /home/shared/Sync/Sites/Clyde_River/Trips/2016/Data_Analysis/Feedline-Path/ vswr-files-pre-work.json None

python ./array_feedline_paths.py '20160701 Clyde River Post-Fix' /home/shared/Sync/Sites/Clyde_River/Trips/2016/DATA/ /home/shared/Sync/Sites/Clyde_River/Trips/2016/Data_Analysis/Feedline-Path/ vswr-files-post-work.json delay-times.json

python ./array_feedline_paths.py '20170811 Inuvik' /home/shared/Sync/Sites/Inuvik/Trips/2017/DATA/ /home/shared/Sync/Sites/Inuvik/Trips/2017/Data_Analysis/Feedline-Path/ vswr-files.json delay-times.json

python ./array_feedline_paths.py '20160705 Rankin Inlet Pre-Fix' /home/shared/Sync/Sites/Rankin_Inlet/Trips/2016/DATA/ /home/shared/Sync/Sites/Rankin_Inlet/Trips/2016/Data_Analysis/Feedline-Path/ vswr-files-pre-work.json None

python ./array_feedline_paths.py '20160721 Rankin Inlet Post-Fix' /home/shared/Sync/Sites/Rankin_Inlet/Trips/2016/DATA/ /home/shared/Sync/Sites/Rankin_Inlet/Trips/2016/Data_Analysis/Feedline-Path/ vswr-files-post-work.json delay-times.json

python ./array_feedline_paths.py '20170627 Saskatoon' /home/shared/Sync/Sites/Saskatoon/SITE-VISITS-2017/DATA/ /home/shared/Sync/Sites/Saskatoon/SITE-VISITS-2017/Data_Analysis/Feedline-Path/ vswr-files.json delay-times.json

