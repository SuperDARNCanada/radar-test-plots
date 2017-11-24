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

# General variables to change depending on data being used
radar_name = sys.argv[1]
data_location = sys.argv[2]
path_file_str = sys.argv[3]

plot_filename = radar_name + ' total-path.png'
plot_title = radar_name + ' Total Phase Path'

print radar_name, data_location, path_file_str, plot_filename

sys.path.append(data_location)


def unwrap_phase(data):
    # take a numpy array with phase_deg and phase_rad datatypes and unwrap.
    if max(data['phase_deg']) < 180.0 and min(data['phase_deg']) > -180.0:
        # unwrap
        for num, entry in enumerate(data['phase_deg']):
            if entry > 355.0 + data['phase_deg'][num - 1]:
                for i in range(num, len(data)):
                    data['phase_deg'][i] = data['phase_deg'][i] - 360.0
                    data['phase_rad'][i] = data['phase_deg'][i] * math.pi / 180.0
            elif entry < -355.0 + data['phase_deg'][num - 1]:
                for i in range(num, len(data)):
                    data['phase_deg'][i] = data['phase_deg'][i] + 360.0
                    data['phase_rad'][i] = data['phase_deg'][i] * math.pi / 180.0


# TODO come up with an interpolation to convert frequency
def correct_frequency_array(dict_of_arrays_with_freq_dtype):

    # find latest starting frequency
    latest_starting_freq = 0
    earliest_ending_freq = 10000000000
    max_data_points = 0
    for path, array in dict_of_arrays_with_freq_dtype.items():
        if array['freq'][0] > latest_starting_freq:
            latest_starting_freq = array['freq'][0]
        if array['freq'][-1] < earliest_ending_freq:
            earliest_ending_freq = array['freq'][-1]
        if array.shape[0] > max_data_points:
            max_data_points = array.shape[0]
            max_array = path

    while dict_of_arrays_with_freq_dtype[max_array]['freq'][0] < latest_starting_freq:
        dict_of_arrays_with_freq_dtype[max_array] = \
            np.delete(dict_of_arrays_with_freq_dtype[max_array], (0), axis=0)

    while dict_of_arrays_with_freq_dtype[max_array]['freq'][-1] > earliest_ending_freq:
        dict_of_arrays_with_freq_dtype[max_array] = \
            np.delete(dict_of_arrays_with_freq_dtype[max_array], (-1), axis=0)

    len_of_new_arrays = dict_of_arrays_with_freq_dtype[max_array].shape[0]
    reference_frequency_array = dict_of_arrays_with_freq_dtype[max_array]['freq']

    new_dict_of_arrays = {}

    short_datasets = []
    long_datasets = {}
    for ant, dataset in dict_of_arrays_with_freq_dtype.items():
        if len(dataset) == min_dataset_length:
            short_datasets.append(ant)
        else:
            long_datasets[ant] = len(dataset)

    for ant in short_datasets:
        for value, entry in enumerate(dict_of_arrays_with_freq_dtype[ant]):
            if entry['freq'] != freqs[value]:
                print entry['freq'], freqs[value]
                sys.exit('Frequencies do not match in datasets - exiting')

    for ant, length in long_datasets.items():
        lines_to_delete = []
        if length % min_dataset_length == 0:
            integer = length/min_dataset_length
            for value, entry in enumerate(dict_of_arrays_with_freq_dtype[ant]):
                if (value-1) % integer != 0:
                    #print entry['freq']
                    lines_to_delete.append(value)
                elif entry['freq'] != freqs[(value-1)/integer]:
                    sys.exit('Datasets are in multiple lengths but frequency axis '
                              'values are not the same when divided, length {} broken down to length '
                              '{}'.format(length, min_dataset_length))
            dict_of_arrays_with_freq_dtype[ant] = np.delete(dict_of_arrays_with_freq_dtype[ant], lines_to_delete, axis=0)
        else:
            sys.exit('Please ensure datasets are the same length and frequency axes '
                     'are the same, length {} is greater than minimum dataset length {}'
                     '{}'.format(length, min_dataset_length, ant))


def get_slope_of_phase_in_nano(phase_data, freq_hz):
    # Freq_hz is list in Hz, phase_data is in rads.
    # dy = np.diff(dataset['phase_rad']) * -10 ** 9 / dx
    # np.insert(dy, [0], delay_freq_list, axis=1)

    if len(freq_hz) != len(phase_data):
        sys.exit('Problem with slope array lengths differ {} {}'.format(len(freq_hz), len(phase_data)))

    freq_data = [i * 2 * math.pi for i in freq_hz]


    # for smoother plot
    dy = []
    for index, entry in enumerate(phase_data):
        if index < 3:
            tslope, intercept, rvalue, pvalue, stderr = stats.linregress(
                freq_data[:(index + 4)],
                phase_data[:(index + 4)])
        elif index >= len(phase_data) - 4:
            tslope, intercept, rvalue, pvalue, stderr = stats.linregress(
                freq_data[(index - 3):],
                phase_data[(index - 3):])
        else:
            tslope, intercept, rvalue, pvalue, stderr = stats.linregress(
                freq_data[(index - 3):(index + 4)],
                phase_data[(index - 3):(index + 4)])
        dy.append(tslope * -10 ** 9)

    dy = np.array(dy)

    return dy


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

    total_path = np.zeros(min_dataset_length, dtype=[('freq', 'i4'), ('phase_deg', 'f4'),
                                                       ('time_ns', 'f4')])

    correct_frequency_array(data)

    total_path['freq'] = reference_frequency_array
    for path, array in data.items():
        total_path['phase_deg'] += array['phase_deg']
        total_path['time_ns'] += array['time_ns']



        # PLOTTING

        numplots = 2
        fig, smpplot = plt.subplots(numplots, sharex=True, figsize=(18, 24))
        xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
        smpplot[numplots - 1].set_xlabel('Frequency (Hz)')
        smpplot[0].set_title(plot_title, fontsize=30)
        smpplot[0].plot(total_path['freq'], total_path['phase_deg'] % 360.0)
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


if __name__ == main():
    main()