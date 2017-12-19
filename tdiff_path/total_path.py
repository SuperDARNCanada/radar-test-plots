#!/usr/bin/python

# total_path.py
# To find the phase paths through the total path

import sys
import time
import fnmatch
import random
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import json
import csv

from dataset_operations.dataset_operations import correct_frequency_array

# General variables to change depending on data being used
radar_name = sys.argv[1]
data_location = sys.argv[2]
path_file_str = sys.argv[3]
time_file_str = sys.argv[4]

plot_filename = radar_name + ' total-path.png'
plot_title = radar_name + ' Total Phase Path'

print radar_name, data_location, path_file_str, plot_filename

sys.path.append(data_location)


def main():
    data_description = []

    data = {}

    for path in ['Feedline-Path', 'Transmitter-Path', 'PM-Path']:
        path_array = np.loadtxt(data_location + path + '/' + path_file_str,
                                dtype=[('freq','i4'), ('phase_deg','f4'), ('time_ns','f4')],
                                delimiter=",",
                                converters={0: lambda x: x[1:], 1: lambda x: x[0:-1],
                                            2: lambda x: x[0:-1]})

        data[path] = path_array

    #print data['Feedline-Path']



    data = correct_frequency_array(data)

    total_path = np.zeros(data['Feedline-Path'].shape[0], dtype=[('freq', 'i4'), ('phase_deg', 'f4'),
                                                       ('time_ns', 'f4')])

    total_path['freq'] = data['Feedline-Path']['freq']
    for path, array in data.items():
        total_path['phase_deg'] += array['phase_deg']
        total_path['time_ns'] += array['time_ns']

    for entry in total_path['phase_deg']:
        if entry > 180:
            entry = -360 + entry


    # PLOTTING

    numplots = 2
    fig, smpplot = plt.subplots(numplots, sharex=True, figsize=(18, 24))
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[numplots - 1].set_xlabel('Frequency (Hz)')
    smpplot[0].set_title(plot_title, fontsize=30)
    smpplot[0].plot(total_path['freq'], total_path['phase_deg'])
    smpplot[0].set_ylabel('Total Path Phase\nDifference b/w Arrays [degrees]')
    smpplot[1].plot(total_path['freq'], total_path['time_ns'])
    smpplot[1].set_ylabel('Total Perceived Time \nDifference b/w Arrays based on Phase [ns]')
    for plot in range(0, numplots):
        smpplot[plot].grid()

    if data_description:
        print data_description
        plt.figtext(0.65, 0.04, data_description, fontsize=8)

    fig.savefig(data_location + 'Total-Path/' + plot_filename)
    plt.close(fig)

    if time_file_str != 'None':
        total_path.tofile(data_location + time_file_str, sep="\n")


if __name__ == main():
    main()