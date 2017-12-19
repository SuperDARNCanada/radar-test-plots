#!/usr/bin/python

# plot_reflection.py
# To plot all reflection data on the same plot.
# This script for if your data is in dB, not SWR format.

import sys
import time
import math
import random
import fnmatch
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import json
import csv

from dataset_operations.dataset_operations import check_frequency_array

# General variables to change depending on data being used
radar_name = sys.argv[1]  # eg. Inuvik
data_location = sys.argv[2]  # eg. '/home/shared/Sync/Sites/Inuvik/Trips/2017/Datasets/'
plot_location = sys.argv[3]  # eg. '/home/shared/Sync/Sites/Inuvik/Trips/2017/Data_Analysis/VSWRs/'
vswr_files_str = sys.argv[4]  # eg. 'vswr-files.json' - must be located in plot_location.
#vswr_intf_files_str = sys.argv[5]  # eg. 'vswr-intf-files.json' - must be location in plot_location.
plot_filename = radar_name + ' vswrs.png'

print radar_name, data_location, plot_location, vswr_files_str, plot_filename

# number_of_data_points = 801
vswrs_plot_title = radar_name + ' Antenna Reflection'

sys.path.append(data_location)

# TODO get date from csv files
with open(plot_location + vswr_files_str) as f:
    vswr_files = json.load(f)

    all_files = vswr_files
#
#
# A list of 21 colors that will be assigned to antennas to keep plot colors consistent.
hex_colors = ['#ff1a1a', '#993300', '#ffff1a', '#666600', '#ff531a', '#cc9900', '#99cc00',
              '#7a7a52', '#004d00', '#33ff33', '#26734d', '#003366', '#33cccc', '#00004d',
              '#5500ff', '#a366ff', '#ff00ff', '#e6005c', '#ffaa80', '#999999']
hex_dictionary = {'other': '#000000'}


def main():
    data_description = []
    missing_data = []
    all_data = {}
    min_dataset_length = 100000  # won't be this high
    for ant, v in all_files.iteritems():
        if ant == '_comment':
            data_description = v
            continue
        if v == 'dne':
            missing_data.append(ant)
            continue
        with open(data_location + v, 'r') as csvfile:
            for line in csvfile:
                if fnmatch.fnmatch(line, 'Freq. [Hz*'):  # skip to header
                    break
            else:  # no break
                sys.exit('No Data in file {}'.format(v))
            row = line.split(',')
            try:
                freq_header = 'Freq*'
                freq_columns = [i for i in range(len(row)) if
                                fnmatch.fnmatch(row[i], freq_header)]
                mag_header = 'Magni*'
                mag_columns = [i for i in range(len(row)) if
                                fnmatch.fnmatch(row[i], mag_header)]
                freq_column = freq_columns[0]
                mag_column = mag_columns[0]
                phase_header = 'Phase*'
                phase_columns = [i for i in range(len(row)) if
                                fnmatch.fnmatch(row[i], phase_header)]
                phase_column = phase_columns[0]
                if (abs(mag_column - freq_column) > 2) or (
                            abs(phase_column - freq_column) > 2):
                    print freq_column, mag_column, phase_column
                    sys.exit('Data Phase and VSWR are given from different sweeps - please'
                                 'check data file so first sweep has SWR and Phase info.')
            except:
                sys.exit('Cannot find VSWR data.')

            next(csvfile)  # skip over header
            csv_reader = csv.reader(csvfile)
            data = []

            for row in csv_reader:
                try:
                    freq = float(row[freq_column])
                    magnitude = float(row[mag_column])
                    phase = float(row[phase_column])
                    data.append((freq, magnitude, phase))
                except:
                    continue
            data = np.array(data, dtype=[('freq', 'i4'), ('dB', 'f4'), ('phase', 'f4')])

            if len(data) < min_dataset_length:
                min_dataset_length = len(data)

            all_data[ant] = data
            hex_dictionary[ant] = hex_colors[0]
            hex_colors.remove(hex_dictionary[ant])

    all_data = check_frequency_array(all_data, min_dataset_length)

    max_phase = list(all_data['M0']['phase'])
    min_phase = list(all_data['M0']['phase'])
    phase_ave = list(all_data['M0']['phase'])
    dB_array = list(all_data['M0']['dB'])
    for ant, dataset in all_data.items():
        for index, entry in enumerate(dataset):
            if entry['phase'] < min_phase[index]:
                min_phase[index] = entry['phase']
            if entry['phase'] > max_phase[index]:
                max_phase[index] = entry['phase']
        if ant == 'M0':
            pass
        else:
            dB_array = [dB_array[i] + dataset['dB'][i] for i in range(len(dataset))]
            phase_ave = [phase_ave[i] + dataset['phase'][i] for i in range(len(dataset))]
    diff_phase = [(max_phase[i] - min_phase[i]) for i in range(len(min_phase))]
    dB_array_ave = [dB_array[i]/16 for i in range(len(dB_array))]
    phase_ave = [phase_ave[i]/16 for i in range(len(phase_ave))]

    # for each antenna, get the linear fit and plot the offset from linear fit.
    linear_fit_dict = {}
    for ant, dataset in all_data.items():
        slope, intercept, rvalue, pvalue, stderr = stats.linregress(dataset['freq'],
                                                                    dataset['phase'])
        linear_fit_dict[ant] = {'slope': slope, 'intercept': intercept, 'rvalue': rvalue,
                                'pvalue': pvalue, 'stderr': stderr}
        offset_of_best_fit = []
        for entry in dataset:
            best_fit_value = slope * entry['freq'] + intercept
            offset_of_best_fit.append(entry['phase'] - best_fit_value)
        linear_fit_dict[ant]['offset_of_best_fit'] = offset_of_best_fit


    # find top antennas with highest phase offsets and plot those antennas SWR
    furthest_phase_offset = {}
    for ant, dataset in all_data.items():
        max_phase_offset = 0
        for index, entry in enumerate(dataset):
            phase_offset = abs(entry['phase'] - phase_ave[index])
            if phase_offset > max_phase_offset:
                max_phase_offset = phase_offset
        furthest_phase_offset[ant] = max_phase_offset
    worst_swrs = []
    while len(worst_swrs) < 5:
        worst_swrs.append(max(furthest_phase_offset, key=lambda key: furthest_phase_offset[key]))
        del furthest_phase_offset[worst_swrs[-1]]

    numplots = 5
    fig, smpplot = plt.subplots(numplots, sharex=True, figsize=(16,22))
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[0].set_title(vswrs_plot_title, size=30, linespacing=1.3)
    for ant, dataset in all_data.items():
        smpplot[0].plot(dataset['freq'], dataset['phase'], label=ant, color=hex_dictionary[ant])
        smpplot[1].plot(dataset['freq'], dataset['dB'], label=ant, color=hex_dictionary[ant])
        smpplot[4].plot(dataset['freq'], linear_fit_dict[ant]['offset_of_best_fit'],
                        label='{}, stderr={}'.format(ant,round(linear_fit_dict[ant]['stderr'], 9)),
                        color=hex_dictionary[ant])
    smpplot[2].plot(all_data['M0']['freq'], diff_phase, label='Max-Min Difference',
                    color=hex_dictionary['other'])
    smpplot[3].plot(all_data['M0']['freq'], dB_array_ave, label='Average SWR',
                    color=hex_dictionary['other'])
    for antenna in worst_swrs:
        smpplot[3].plot(all_data[antenna]['freq'], all_data[antenna]['dB'], label=antenna,
                        color=hex_dictionary[antenna])
        smpplot[2].plot(all_data[antenna]['freq'], all_data[antenna]['phase'] - phase_ave,
                        label=antenna, color=hex_dictionary[antenna])
    smpplot[4].set_xlabel('Frequency (Hz)', size='xx-large')
    smpplot[0].set_ylabel('Phase [degrees]', size='xx-large')
    smpplot[1].set_ylabel('Magnitude [dB]', size='xx-large')
    smpplot[2].set_ylabel('Worst Phase Offsets\n from Average', size='xx-large')
    smpplot[3].set_ylabel('Worst Magnitudes by Phase', size='xx-large')
    for i in range(0, numplots):
        smpplot[i].grid()
    smpplot[2].legend(fontsize=10)
    smpplot[3].legend(fontsize=10)
    smpplot[4].legend(fontsize=7)
    smpplot[4].set_ylabel('Phase Offsets from\nLine of Best Fit', size='xx-large')
    #plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
    #           ncol=2, mode="expand", borderaxespad=0.)
    print "plotting"
    if missing_data:  # not empty
        missing_data_statement = "***MISSING DATA FROM ANTENNA(S) "
        for element in missing_data:
            missing_data_statement = missing_data_statement + element + " "
        print missing_data_statement
        plt.figtext(0.65, 0.05, missing_data_statement, fontsize=15)

    if data_description:
        print data_description
        plt.figtext(0.65, 0.10, data_description, fontsize=15)

    fig.savefig(plot_location + plot_filename)
    plt.close(fig)


if __name__ == main():
    main()
