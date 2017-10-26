#!/usr/bin/python

# plot_vswrs.py
# To plot all VSWR data on the same plot to visualize
# differences between the antennas.

import sys
import time
import math
import numpy as np
import matplotlib.pyplot as plt

#
#
# General variables to change depending on data being used
#
radar_name = 'Inuvik'
data_location = '/home/shared/Sync/Sites/Inuvik/Trips/2017/Datasets/'
plot_location = '/home/shared/Sync/Sites/Inuvik/Trips/2017/Data_Analysis/Plots/'
plot_filename = 'vswrs.png'
number_of_data_points = 801
vswr_main_files = {1: '0702.csv', 2: '0703.csv', 3: '0704.csv', 4: '0705.csv', 5: '0706.csv',
                   6: '0707.csv', 7: '0708.csv', 8: '0709.csv', 9: '0710.csv', 10: '0711.csv',
                   11: '0712.csv', 12: '0713.csv', 13: '0714.csv', 14: '0715.csv', 15: '0716.csv',
                   16: '0717.csv'}
vswr_intf_files = {1: '0718.csv', 2: '0719.csv', 3: '0720.csv', 4: '0721.csv'}
vswrs_plot_title = radar_name + ' Feedline to Antenna Standing Wave Ratios'

all_files = [vswr_main_files, vswr_intf_files]

data_description = 'This data was taken on site visits in August 2017.'

#
#

def main():
    main_data = {}
    intf_data = {}
    for j in range(len(all_files)):
        for i in all_files[j].keys():
            with open(data_location + vswr_main_files[i], 'r') as csvfile:
                lines = csvfile.readlines()
                for ln in lines:
                    if ln.find('Freq. [Hz]') != -1:  # found the right line
                        header_line = ln
                        first_line_of_data = lines.index(header_line) + 1
                        break
                find_phase = header_line.split(",", 16)
                # print find_phase
                freq_column = find_phase.index('Freq. [Hz]')
                vswr_column = find_phase.index('VSWR [(VSWR)]')
                phase_value = 'Phase [\xb0]'
                try:
                    phase_column = find_phase.index(phase_value)
                except ValueError:
                    phase_value = 'Phase [\xef\xbf\xbd]'
                    phase_column = find_phase.index(phase_value)
                it = 0
                while (abs(vswr_column - freq_column) > 2) or (abs(phase_column - freq_column) > 2):
                    # data is from different sweeps (not the first sweep)
                    find_phase.remove('')
                    find_phase.remove(find_phase[2])
                    find_phase.remove(find_phase[1])
                    find_phase.remove(find_phase[0])
                    # print find_phase
                    it = it + 1
                    freq_column = find_phase.index('Freq. [Hz]') + 4 * it
                    vswr_column = find_phase.index('VSWR [(VSWR)]') + 4 * it
                    phase_column = find_phase.index(phase_value) + 4 * it
                # print freq_column, vswr_column, phase_column
                if j == 0: # we are in vswr_main_files
                    main_data[i] = np.zeros((number_of_data_points,),
                                            dtype=[('freq', 'i4'), ('VSWR', 'f4'),
                                                   ('phase', 'f4')])
                    for ln in range(first_line_of_data, first_line_of_data + number_of_data_points):
                        data = lines[ln].split(",", 16)
                        main_data[i][ln - first_line_of_data] = (data[freq_column],
                                                                 float(data[vswr_column]),
                                                                 float(data[phase_column]))
                else:  # in vswr_intf_files
                    intf_data[i] = np.zeros((number_of_data_points,),
                                            dtype=[('freq', 'i4'), ('VSWR', 'f4'),
                                                   ('phase', 'f4')])
                    for ln in range(first_line_of_data, first_line_of_data + number_of_data_points):
                        data = lines[ln].split(",", 16)
                        intf_data[i][ln - first_line_of_data] = (data[freq_column],
                                                                 float(data[vswr_column]),
                                                                 float(data[phase_column]))

    fig, smpplot = plt.subplots(2, sharex=True)
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[0].set_title(vswrs_plot_title)
    for ant, dataset in main_data.items():
        smpplot[0].plot(dataset['freq'], dataset['phase'])
        smpplot[1].plot(dataset['freq'], dataset['VSWR'])
    for ant, dataset in intf_data.items():
        smpplot[0].plot(dataset['freq'], dataset['phase'])
        smpplot[1].plot(dataset['freq'], dataset['VSWR'])
    smpplot[1].set_xlabel('Frequency (Hz)')
    smpplot[0].set_ylabel('S11 Phase of\nAntennas [degrees]')
    smpplot[1].set_ylabel('VSWR]')  # referenced to power at a single antenna
    smpplot[0].grid()
    smpplot[1].grid()
    print "plotting"
    fig.savefig(plot_location + plot_filename)
    plt.close(fig)
# TODO add legend

# TODO add plot of phase differences


main()