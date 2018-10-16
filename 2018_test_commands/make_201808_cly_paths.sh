#!/bin/bash

MY_DIR=`dirname "$(readlink -f "$0")"`
echo $MY_DIR
cd $MY_DIR
cd ../tdiff_path/

BASE_DIR="/home/shared/Sync/Sites/Clyde_River/Trips/2018/"
DATA_DIR="${BASE_DIR}Data-wo-UTF8/"
OUTPUT_DIR="${BASE_DIR}Data_Analysis/"
DESCRIPTOR='Clyde-River-2018'
FIXED_DESCRIPTOR='Clyde-River-Fixed-2018'

python3 ./plot_vswrs.py $DESCRIPTOR $DATA_DIR $OUTPUT_DIR cly_2018_vswrs.json

python3 ./plot_vswrs.py $FIXED_DESCRIPTOR $DATA_DIR $OUTPUT_DIR cly_2018_fixed_vswrs.json

python3 ./array_feedline_paths.py $DESCRIPTOR $DATA_DIR $OUTPUT_DIR cly_2018_fixed_vswrs.json '-delays.txt'

python3 ./transmitter_paths.py $DESCRIPTOR $DATA_DIR $OUTPUT_DIR cly_tx_rcv.json '-delays.txt'

python3 ./phasing_matrix_paths.py $DESCRIPTOR $DATA_DIR $OUTPUT_DIR cly_pm_paths.json '-delays.txt'

python3 ./phasing_matrix_paths.py $FIXED_DESCRIPTOR $DATA_DIR $OUTPUT_DIR cly_fixed_pm_paths.json '-delays.txt'

python3 ./total_path_tdiff.py $DESCRIPTOR $OUTPUT_DIR '-delays.txt'

#python ./total_path_arrays.py '201808 Rankin Inlet' $OUTPUT_DIR

