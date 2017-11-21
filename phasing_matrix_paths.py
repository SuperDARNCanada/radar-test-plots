#!/usr/bin/python

# phasing_matrix_paths.py
# To find the phase paths through the phasing matrix.

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
plot_location = sys.argv[3]
path_file_str = sys.argv[4]
time_file_str = sys.argv[5]

plot_filename = radar_name + ' PM-path.png'
plot_title = radar_name + ' Phasing Matrix Paths'

print radar_name, data_location, plot_location, path_file_str, plot_filename

sys.path.append(data_location)

with open(plot_location + path_file_str) as f:
    path_files = json.load(f)

# A list of 21 colors that will be assigned to antennas to keep plot colors consistent.
hex_colors = ['#ff1a1a', '#993300', '#ffff1a', '#666600', '#ff531a', '#cc9900', '#99cc00',
              '#7a7a52', '#004d00', '#33ff33', '#26734d', '#003366', '#33cccc', '#00004d',
              '#5500ff', '#a366ff', '#ff00ff', '#e6005c', '#ffaa80', '#999999']
hex_dictionary = {'other': '#000000'}


def combine_arrays(array_dict):

    one_array_key = random.choice(array_dict.keys())

    for k, v in array_dict.iteritems():
        for a, b in zip(array_dict[one_array_key], v):
            if a['freq'] != b['freq']:
                errmsg = "Frequencies not Equal {} {}".format(a['freq'], b['freq'])
                sys.exit(errmsg)

    # now we have data points at same frequencies.
    # next - sum signals.
    #number_of_data_points = len(array_dict[one_array_key])

    combined_array = np.copy(array_dict[one_array_key])

    for k, v in array_dict.iteritems():
        # print k
        if k == one_array_key:
            continue  # skip, do not add
        for c, a in zip(combined_array, v):
            if c['freq'] != a['freq']:
                errmsg = "Frequencies not Equal"
                sys.exit(errmsg)

            # convert to rads - negative because we are using proof using cos(x-A)
            phase_rads1 = -(c['phase_rad'] % (2 * math.pi))
            phase_rads2 = -(a['phase_rad'] % (2 * math.pi))

            # we want voltage amplitude so use /20
            amplitude_1 = 10 ** (c['magnitude'] / 20)
            amplitude_2 = 10 ** (a['magnitude'] / 20)

            combined_amp_squared = (
                amplitude_1 ** 2 + amplitude_2 ** 2 + 2 * amplitude_1 * amplitude_2 * math.cos(
                    phase_rads1 - phase_rads2))
            combined_amp = math.sqrt(combined_amp_squared)
            # we based it on amplitude of 1 at each antenna.
            c['magnitude'] = 20 * math.log(combined_amp, 10)
            combined_phase = math.atan2(
                amplitude_1 * math.sin(phase_rads1) + amplitude_2 * math.sin(phase_rads2),
                amplitude_1 * math.cos(phase_rads1) + amplitude_2 * math.cos(phase_rads2))

            # this is negative so make it positive cos(x-theta)
            c['phase_rad'] = -combined_phase
            c['phase_deg'] = -combined_phase * 360.0 / (2.0 * math.pi)

    # unwrap the phase of the phase_rad array
    for index, entry in enumerate(combined_array):
        if index != 0:
            if entry['phase_rad'] >= (2 * math.pi) + combined_array[index-1]['phase_rad'] - 1.0:  # a couple degrees
                for new_index in range(index, combined_array.shape[0]):
                    combined_array[new_index]['phase_rad'] = combined_array[new_index]['phase_rad'] - (2 * math.pi)
            elif entry['phase_rad'] <= -(2 * math.pi) + combined_array[index-1]['phase_rad'] + 0.40:  # a couple degrees
                for new_index in range(index, combined_array.shape[0]):
                    combined_array[new_index]['phase_rad'] = combined_array[new_index]['phase_rad'] + (2 * math.pi)
    return combined_array


def check_frequency_array(dict_of_arrays_with_freq_dtype, min_dataset_length):
    short_datasets = []
    long_datasets = {}
    for ant, dataset in dict_of_arrays_with_freq_dtype.items():
        if len(dataset) == min_dataset_length:
            short_datasets.append(ant)
        else:
            long_datasets[ant] = len(dataset)

    for ant in short_datasets:
        for value, entry in enumerate(dict_of_arrays_with_freq_dtype[ant]):
            if entry['freq'] != dict_of_arrays_with_freq_dtype[short_datasets[0]][value]['freq']:
                sys.exit('Frequencies do not match in datasets - exiting')

    for ant, length in long_datasets.items():
        lines_to_delete = []
        if length % min_dataset_length == 0:
            integer = length/min_dataset_length
            for value, entry in enumerate(dict_of_arrays_with_freq_dtype[ant]):
                if (value-1) % integer != 0:
                    #print entry['freq']
                    lines_to_delete.append(value)
                elif entry['freq'] != dict_of_arrays_with_freq_dtype[short_datasets[0]][(value-1)/integer]['freq']:
                    sys.exit('Datasets are in multiple lengths but frequency axis '
                              'values are not the same when divided, length {} broken down to length '
                              '{}'.format(length, min_dataset_length))
            dict_of_arrays_with_freq_dtype[ant] = np.delete(dict_of_arrays_with_freq_dtype[ant], lines_to_delete, axis=0)
        else:
            sys.exit('Please ensure datasets are the same length and frequency axes '
                     'are the same, length {} is greater than minimum dataset length '
                     '{}'.format(length, min_dataset_length))


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
    attenuator_flag = False
    combined_test_data_flag = False
    missing_data = []
    estimate_data = []
    main_data = {}
    intf_data = {}
    min_dataset_length = 100000  # just a big number
    for k, v in path_files.iteritems():
        if k == '_comment':
            data_description = v
            continue
        if v == 'dne':
            missing_data.append(k)
            continue
        if v == 'estimate_intf':
            estimate_data.append(k) # TODO estimate with a given slope
            continue
        with open(data_location + v, 'r') as csvfile:
            for line in csvfile:
                if fnmatch.fnmatch(line, 'Freq. [Hz*'):  # skip to header
                    break
            else:  # no break
                sys.exit('No Data in file {}'.format(v))
            row = line.split(',')
            try:
                freq_header = '*Freq*'
                freq_columns = [i for i in range(len(row)) if
                                fnmatch.fnmatch(row[i], freq_header)]
                magnitude_header = '*Magnit*'
                magnitude_columns = [i for i in range(len(row)) if
                                fnmatch.fnmatch(row[i], magnitude_header)]
                freq_column = freq_columns[0]
                magnitude_column = magnitude_columns[0]
                phase_header = '*Phase*'
                phase_columns = [i for i in range(len(row)) if
                                fnmatch.fnmatch(row[i], phase_header)]
                phase_column = phase_columns[0]
            except:
                sys.exit('Cannot find data {}.'.format(v))
            i = 0
            while (abs(magnitude_column - freq_column) > 2) or (abs(phase_column - freq_column) > 2):
                i += 1
                try:
                    freq_column = freq_columns[i]
                    if magnitude_column > phase_column:
                        phase_column = phase_columns[i]
                    if phase_column > magnitude_column:
                        magnitude_column = magnitude_columns[i]
                except:
                    sys.exit('Data Phase and Magnitude are given from different sweeps.')
            next(csvfile)  # skip over header
            csv_reader = csv.reader(csvfile)

            data = []
            for row in csv_reader:
                try:
                    freq = float(row[freq_column])
                    mag = float(row[magnitude_column])
                    phase = float(row[phase_column])
                except:
                    continue
                phase_rad = float(phase) * math.pi / 180.0
                data.append((freq, mag, float(phase), phase_rad))
            data = np.array(data, dtype=[('freq', 'i4'), ('magnitude', 'f4'),
                                         ('phase_deg', 'f4'), ('phase_rad', 'f4')])

            if len(data) < min_dataset_length:
                min_dataset_length = len(data)

            if k[0] == 'M':  # in main files.
                if k == 'M_combined':
                    combined_main_array_test = data
                else:
                    main_data[k] = data
                    hex_dictionary[k] = hex_colors[0]
                    hex_colors.remove(hex_dictionary[k])
            elif k[0] == 'I':  # in intf files
                if k == 'I_combined':
                    combined_intf_array_test = data
                else:
                    intf_data[k] = data
                    hex_dictionary[k] = hex_colors[0]
                    hex_colors.remove(hex_dictionary[k])
            elif k == 'atten':
                attenuator_flag = True
                atten_data = data
            else:
                sys.exit('There is an invalid key {}'.format(k))

    if attenuator_flag:
        # remove this data from all datasets.
        # TODO

    if combined_intf_array_test and combined_main_array_test:
        combined_test_data_flag = True

    check_frequency_array(main_data, min_dataset_length)
    combined_main_array = combine_arrays(main_data)

    linear_fit_dict = {}
    # combined main array slope
    main_slope, main_intercept, rvalue, pvalue, stderr = stats.linregress(combined_main_array['freq'],
                                                                combined_main_array['phase_rad'])
    offset_of_best_fit = []
    for entry in combined_main_array:
        best_fit_value = main_slope * entry['freq'] + main_intercept
        offset_of_best_fit.append(entry['phase_rad'] - best_fit_value)
    linear_fit_dict['M_all'] = {'slope': main_slope, 'intercept': main_intercept, 'rvalue': rvalue,
                                'pvalue': pvalue, 'stderr': stderr,
                                'offset_of_best_fit': np.array(offset_of_best_fit),
                                'time_delay_ns': round(main_slope / (2 * math.pi), 11) * -10 ** 9}

    # TODO if intf_data is empty!
    if not intf_data:  # if empty
        if estimate_data:  # if not empty
            data = []
            for i in range(0, min_dataset_length):
                freq = 8000000 + (12000000/(min_dataset_length - 1)) * i
                phase_rad = main_slope * freq + main_intercept  # this is slope of combined main array
                phase_deg = (phase_rad * 180.0 / math.pi) % 360
                if phase_deg > 180.0:
                    phase_deg = phase_deg - 360.0
                data.append((freq, 0.0, phase_deg, phase_rad))
            intf_data = {'I0': np.array(data, dtype=[('freq', 'i4'), ('magnitude', 'f4'),
                                              ('phase_deg', 'f4'), ('phase_rad', 'f4')])}
            hex_dictionary['I0'] = hex_colors[0]
            hex_colors.remove(hex_dictionary['I0'])
        else:
            data = []
            for i in range(0, min_dataset_length):
                freq = 8000000 + (12000000/(min_dataset_length - 1)) * i
                data.append((freq, 0.0, 0.0, 0.0))
            intf_data = {'I0': np.array(data, dtype=[('freq', 'i4'), ('magnitude', 'f4'),
                                              ('phase_deg', 'f4'), ('phase_rad', 'f4')])}
            hex_dictionary['I0'] = hex_colors[0]
            hex_colors.remove(hex_dictionary['I0'])

    check_frequency_array(intf_data, min_dataset_length)

    all_data = main_data.copy()
    all_data.update(intf_data)

    # for each antenna, get the linear fit and plot the offset from linear fit.

    for ant, dataset in all_data.items():
        slope, intercept, rvalue, pvalue, stderr = stats.linregress(dataset['freq'],
                                                                    dataset['phase_rad'])
        linear_fit_dict[ant] = {'slope': slope, 'intercept': intercept, 'rvalue': rvalue,
                                'pvalue': pvalue, 'stderr': stderr}
        offset_of_best_fit = []
        for entry in dataset:
            best_fit_value = slope * entry['freq'] + intercept
            offset_of_best_fit.append(entry['phase_rad'] - best_fit_value)
        linear_fit_dict[ant]['offset_of_best_fit'] = np.array(offset_of_best_fit)
        linear_fit_dict[ant]['time_delay_ns'] = round(slope / (2 * math.pi), 11) * -10 ** 9

    combined_intf_array = combine_arrays(intf_data)

    # combined intf array slope
    slope, intercept, rvalue, pvalue, stderr = stats.linregress(combined_intf_array['freq'],
                                                                combined_intf_array['phase_rad'])
    offset_of_best_fit = []
    for entry in combined_intf_array:
        best_fit_value = slope * entry['freq'] + intercept
        offset_of_best_fit.append(entry['phase_rad'] - best_fit_value)
    linear_fit_dict['I_all'] = {'slope': slope, 'intercept': intercept, 'rvalue': rvalue,
                                'pvalue': pvalue, 'stderr': stderr,
                                'offset_of_best_fit': np.array(offset_of_best_fit),
                                'time_delay_ns': round(slope / (2 * math.pi), 11) * -10 ** 9}

    array_diff = []
    for m, i in zip(combined_main_array, combined_intf_array):
        freq = i['freq']
        phase = ((m['phase_deg'] - i['phase_deg']) % 360)
        if phase > 180:
            phase = -360 + phase
        time_ns = phase * 10**9 / (freq * 360.0)
        array_diff.append((freq, phase, time_ns))
    array_diff = np.array(array_diff, dtype=[('freq', 'i4'), ('phase_deg', 'f4'),
                                             ('time_ns', 'f4')])

    if time_file_str != 'None':  # for pre-fix files, for now
        with open(plot_location + time_file_str, 'w') as time_file:
            time_file.write(str(array_diff))
    # PLOTTING

    numplots = 6
    fig, smpplot = plt.subplots(numplots, sharex=True, figsize=(18, 24))
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[numplots - 1].set_xlabel('Frequency (Hz)')
    smpplot[0].set_title(plot_title, fontsize=30)
    smpplot[0].plot(combined_main_array['freq'], combined_main_array['phase_deg'],
                    color=hex_dictionary['M0'], label='Main Array Calculated')
    smpplot[1].plot(combined_main_array['freq'], combined_main_array['magnitude'],
                    color=hex_dictionary['M0'], label='Main Array Calculated')
    smpplot[0].plot(combined_intf_array['freq'], combined_intf_array['phase_deg'],
                    color=hex_dictionary['I0'], label='Intf Array Calculated')
    smpplot[1].plot(combined_intf_array['freq'], combined_intf_array['magnitude'],
                    color=hex_dictionary['I0'], label='Intf Array Calculated')
    # TODO input combined from test and plot as well.

    smpplot[0].set_ylabel('Receiver Phasing Matrix Path of\nArrays [degrees]')  # from antenna to feedline end at building.
    smpplot[1].set_ylabel('Combined\nArrays [dB]')  # referenced to power at a single antenna

    for plot in range(0, numplots):
        smpplot[plot].grid()
    print "plotting"
    smpplot[2].plot(array_diff['freq'], array_diff['phase_deg'],
                    label='Calculated Arrays Difference')
    # TODO plot difference from tested arrays.
    smpplot[2].set_ylabel('Phasing Matrix Path\nDifference Between\nArrays [degrees]')

    for ant, dataset in all_data.items():
        if ant[0] == 'M':  # plot with main array
            smpplot[3].plot(dataset['freq'], linear_fit_dict[ant]['offset_of_best_fit'] * 180.0 / math.pi,
                            label='{}, delay={} ns'.format(ant,
                                                           linear_fit_dict[ant]['time_delay_ns']),
                            color=hex_dictionary[ant])
        elif ant[0] == 'I':
            smpplot[4].plot(dataset['freq'], linear_fit_dict[ant]['offset_of_best_fit'] * 180.0 / math.pi,
                            label='{}, delay={} ns'.format(ant,
                                                           linear_fit_dict[ant]['time_delay_ns']),
                            color=hex_dictionary[ant])

    smpplot[3].plot(all_data['M0']['freq'], linear_fit_dict['M_all']['offset_of_best_fit'] * 180.0 / math.pi,
                    color=hex_dictionary['other'], label='Combined Main, delay={} ns'.format(linear_fit_dict['M_all']['time_delay_ns']))  # plot last
    smpplot[4].plot(all_data['M0']['freq'], linear_fit_dict['I_all']['offset_of_best_fit'] * 180.0 / math.pi,
                    color=hex_dictionary['other'], label='Combined Intf, delay={} ns'.format(linear_fit_dict['I_all']['time_delay_ns']))  # plot last


    smpplot[3].legend(fontsize=10, ncol=4)
    smpplot[4].legend(fontsize=12)
    smpplot[3].set_ylabel('Phasing Matrix Main Paths Offset\n from Own Line of Best\nFit [degrees]')
    smpplot[4].set_ylabel('Phasing Matrix Intf Paths Offset\n from Own Line of Best\nFit [degrees]')
    # TODO plot time for all paths based on phase and plot actual tested combined paths.
    smpplot[5].set_ylabel('Perceived Time\nDifference b/w arrays\n Based on Phase [ns]')
    smpplot[5].plot(array_diff['freq'], array_diff['time_ns'])

    if missing_data:  # not empty
        missing_data_statement = "***MISSING DATA FROM ANTENNA(S) "
        for element in missing_data:
            missing_data_statement = missing_data_statement + element + " "
        print missing_data_statement
        plt.figtext(0.65, 0.05, missing_data_statement, fontsize=15)

    if estimate_data:  # not empty
        estimate_data_statement = "***ESTIMATED INTF DATA BECAUSE MISSING MEASUREMENT"
        print estimate_data_statement
        plt.figtext(0.55, 0.05, estimate_data_statement, fontsize=15)

    if data_description:
        print data_description
        plt.figtext(0.65, 0.10, data_description, fontsize=15)

    fig.savefig(plot_location + plot_filename)
    plt.close(fig)


if __name__ == main():
    main()
