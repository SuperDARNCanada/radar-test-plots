#!/usr/bin/python

# for plotting 2009 vs 2017 data. special case where we only have phase
# for 2009 antenna data.

import sys
import fnmatch
import numpy as np
import matplotlib.pyplot as plt
from scipy import constants
import json
import csv

from tdiff_path.dataset_operations.dataset_operations import wrap_phase_dictionary, \
    interp_frequency_array

# General variables to change depending on data being used
radar_name = sys.argv[1]  # eg. Inuvik
# eg. '/home/shared/Sync/Sites/Inuvik/Trips/2017/Datasets/'
data_location = sys.argv[2]
# eg. '/home/shared/Sync/Sites/Inuvik/Trips/2017/Data_Analysis/VSWRs/'
plot_location = sys.argv[3]
before_fixes_data_file = sys.argv[4]
before_data_file = sys.argv[5]  # eg. 'files.json' located in plot_location.
after_files_str = sys.argv[6]  # eg. 'files.json' located in plot_location.
plot_filename = radar_name + ' changes.png'

print(radar_name, data_location, plot_location, plot_filename)

# number_of_data_points = 801
vswrs_plot_title = radar_name + ' Antenna Reflection'

sys.path.append(data_location)

# TODO get date from csv files

with open(plot_location + after_files_str) as f:
    after_files = json.load(f)
#
#
# A list of 21 colors that will be assigned to antennas to keep plot
# colors consistent.
hex_colors = [
    '#ff1a1a',
    '#993300',
    '#ffff1a',
    '#666600',
    '#ff531a',
    '#cc9900',
    '#99cc00',
    '#7a7a52',
    '#004d00',
    '#33ff33',
    '#26734d',
    '#003366',
    '#33cccc',
    '#00004d',
    '#5500ff',
    '#a366ff',
    '#ff00ff',
    '#e6005c',
    '#ffaa80',
    '#999999']
hex_dictionary = {'other': '#000000'}


def main():
    data_description = []
    missing_data = []
    before_data = {}
    before_fixes_data = {}
    after_data = {}
    after_data_with_15m_removed = {}
    min_dataset_length = 100000  # won't be this high

    freq_column = 0
    for ant in range(0, 16):
        with open(data_location + before_data_file, 'r') as csvfile:
            next(csvfile)  # skip over header
            csv_reader = csv.reader(csvfile)
            data = []
            for row in csv_reader:
                freq = float(row[freq_column])
                phase = float(row[ant + 1])
                data.append((freq, phase))
            data = np.array(data, dtype=[('freq', 'i4'), ('phase', 'f4')])

            if len(data) < min_dataset_length:
                min_dataset_length = len(data)

            before_data['M' + str(ant)] = data
            hex_dictionary['M' + str(ant)] = hex_colors[0]
            hex_colors.remove(hex_dictionary['M' + str(ant)])

    for ant in range(0, 16):
        with open(data_location + before_fixes_data_file, 'r') as csvfile:
            next(csvfile)  # skip over header
            csv_reader = csv.reader(csvfile)
            data = []
            print(ant + 1)
            for row in csv_reader:
                freq = float(row[freq_column])
                phase = float(row[ant + 1])
                data.append((freq, phase))
            data = np.array(data, dtype=[('freq', 'i4'), ('phase', 'f4')])

            if len(data) < min_dataset_length:
                min_dataset_length = len(data)

            before_fixes_data['M' + str(ant)] = data

    for ant, v in after_files.iteritems():
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
                    print(freq_column, mag_column, phase_column)
                    sys.exit(
                        'Data Phase and Magnitude are given from different sweeps - please'
                        'check data file so first sweep has SWR and Phase info.')
            except BaseException:
                sys.exit('Cannot find data fields.')

            next(csvfile)  # skip over header
            csv_reader = csv.reader(csvfile)
            data = []

            for row in csv_reader:
                try:
                    freq = float(row[freq_column])
                    magnitude = float(row[mag_column])
                    phase = float(row[phase_column])
                    data.append((freq, magnitude, phase))
                except BaseException:
                    continue
            data = np.array(
                data, dtype=[
                    ('freq', 'i4'), ('dB', 'f4'), ('phase', 'f4')])

            if len(data) < min_dataset_length:
                min_dataset_length = len(data)

            after_data[ant] = data

    after_data = interp_frequency_array(after_data)

    velocity_factor = 0.66
    cable_distance = 22.1
    slope_15m = -360.0 * cable_distance / \
        (constants.speed_of_light * velocity_factor)
    starting_freq = after_data['M0']['freq'][0]
    starting_phase = (starting_freq * slope_15m * 2) % 360.0
    if starting_phase > 180.0:
        starting_phase = starting_phase - 360.0

    for ant, dataset in after_data.items():
        data = []
        for num, freq in enumerate(dataset['freq']):
            data.append(
                (freq, (dataset['phase'][num] - ((freq - starting_freq) * slope_15m * 2 + starting_phase))))
        after_data_with_15m_removed[ant] = np.array(
            data, dtype=[('freq', 'i4'), ('phase', 'f4')])

    fig1, smpplot = plt.subplots(3, sharex=True, figsize=(16, 22))
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[0].set_title(vswrs_plot_title, size=30, linespacing=1.3)
    for ant, dataset in before_data.items():
        smpplot[0].plot(
            dataset['freq'],
            dataset['phase'],
            label=ant,
            color=hex_dictionary[ant])
    for ant, dataset in after_data_with_15m_removed.items():
        smpplot[1].plot(
            dataset['freq'],
            dataset['phase'],
            label=ant,
            color=hex_dictionary[ant])
    for ant, dataset in after_data.items():
        smpplot[2].plot(
            dataset['freq'],
            dataset['dB'],
            label=ant,
            color=hex_dictionary[ant])
    smpplot[2].set_xlabel('Frequency (Hz)', size='xx-large')
    smpplot[0].set_ylabel('2009 Phase [degrees]', size='xx-large')
    smpplot[1].set_ylabel('2017 Phase [degrees]', size='xx-large')
    smpplot[2].set_ylabel('2017 Magnitude [dB]', size='xx-large')
    for i in range(0, 3):
        smpplot[i].grid()
    smpplot[0].legend(fontsize=10)

    fig1.savefig(plot_location + plot_filename)
    plt.close(fig1)

    # wrapped datasets
    before_fixes_data_wrapped = wrap_phase_dictionary(before_fixes_data)
    before_data_wrapped = wrap_phase_dictionary(before_data)
    after_data_with_15m_removed_wrapped = wrap_phase_dictionary(
        after_data_with_15m_removed)

    for ant, dataset in before_data.items():
        fig, newplot = plt.subplots()
        newplot.plot(
            before_fixes_data[ant]['freq'],
            before_fixes_data[ant]['phase'],
            label='2009 before fixes',
            color='m')
        newplot.plot(
            dataset['freq'],
            dataset['phase'],
            label='2009 after fixes',
            color='b')
        newplot.plot(
            after_data[ant]['freq'],
            after_data[ant]['phase'],
            label='20171212',
            color='r')
        newplot.plot(
            after_data_with_15m_removed[ant]['freq'],
            after_data_with_15m_removed[ant]['phase'],
            label='20171212, cable removed',
            color='g')
        newplot.grid()
        newplot.legend()
        fig.savefig(plot_location + 'antennas-separate/' + ant + '.png')
        plt.close(fig)

        fig2, wrapped_plot = plt.subplots()
        wrapped_plot.plot(
            before_data_wrapped[ant]['freq'],
            before_data_wrapped[ant]['phase'],
            label='2009 after fixes',
            color='b')
        wrapped_plot.plot(
            after_data_with_15m_removed_wrapped[ant]['freq'],
            after_data_with_15m_removed_wrapped[ant]['phase'],
            label='20171212, cable removed',
            color='g')
        wrapped_plot.grid()
        wrapped_plot.legend()
        fig2.savefig(plot_location + 'antennas-separate-wrapped/' + ant + '.png')
        plt.close(fig2)
    if data_description:
        print(data_description)
        plt.figtext(0.65, 0.10, data_description, fontsize=15)


if __name__ == main():
    main()
