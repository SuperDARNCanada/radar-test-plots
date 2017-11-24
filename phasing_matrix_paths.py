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
array_colors = {'main': '#ff1a1a', 'intf': '#993300', 'main_test': '#33cccc', 'intf_test': '#e6005c'}


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

    unwrap_phase(combined_array)
    return combined_array


def check_frequency_array(dict_of_arrays_with_freq_dtype, min_dataset_length, freqs):
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
    atten_data = {}
    attenuation = 0.0
    data_description = []
    attenuator_flag = False
    combined_test_data_flag = False
    combined_array_test = {}
    missing_data = []
    estimate_data = []
    main_data = {}
    intf_data = {}
    min_dataset_length = 100000  # just a big number
    for k, v in path_files.iteritems():
        if k == '_comment':
            data_description = v
            continue
        if k == 'atten':
            attenuator_flag = True
            attenuation = float(v)
            continue
        if v == 'dne':
            missing_data.append(k)
            continue
        if v == 'estimate_intf':
            estimate_data.append(k)  # TODO estimate with a given slope
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

            # unwrap
            unwrap_phase(data)

            if len(data) < min_dataset_length:
                min_dataset_length = len(data)
                min_data_freqs = data['freq'] # reference frequency sequence.

            if k[0] == 'M':  # in main files.
                if k == 'M_combined':
                    combined_array_test['main_combined'] = data
                else:
                    main_data[k] = data
                    hex_dictionary[k] = hex_colors[0]
                    hex_colors.remove(hex_dictionary[k])
            elif k[0] == 'I':  # in intf files
                if k == 'I_combined':
                    combined_array_test['intf_combined'] = data
                else:
                    intf_data[k] = data
                    hex_dictionary[k] = hex_colors[0]
                    hex_colors.remove(hex_dictionary[k])
            elif k == 'atten_file':
                attenuator_flag = True
                atten_data = {'atten' : data}
            else:
                sys.exit('There is an invalid key {}'.format(k))

    check_frequency_array(main_data, min_dataset_length, min_data_freqs)
    check_frequency_array(atten_data, min_dataset_length, min_data_freqs)
    check_frequency_array(combined_array_test, min_dataset_length, min_data_freqs)

    if attenuator_flag:
        if atten_data:
            for datadict in [main_data, intf_data, combined_array_test]:
                for ant, dataset in datadict.items():
                    for num, entry in enumerate(dataset):
                        entry['phase_deg'] = entry['phase_deg'] - atten_data['atten'][num]['phase_deg']
                        entry['magnitude'] = entry['magnitude'] - atten_data['atten'][num]['magnitude']
                        entry['phase_rad'] = entry['phase_rad'] - atten_data['atten'][num]['phase_rad']
        else:  # float attenuation
            for datadict in [main_data, intf_data, combined_array_test]:
                for ant, dataset in datadict.items():
                    for num, entry in enumerate(dataset):
                        entry['magnitude'] = entry['magnitude'] - attenuation
                        # phase will not change, in this way phase difference is still accurate
                        # since all paths had the attenuator phase change in the measurement.

    if combined_array_test:
        combined_test_data_flag = True

    if main_data:
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

        check_frequency_array(intf_data, min_dataset_length, min_data_freqs)

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
        array_diff_dict = {'calculated': array_diff}

        if combined_test_data_flag:
            array_diff = []
            for m, i in zip(combined_array_test['main_combined'], combined_array_test['intf_combined']):
                freq = i['freq']
                phase = ((m['phase_deg'] - i['phase_deg']) % 360)
                if phase > 180:
                    phase = -360 + phase
                time_ns = phase * 10**9 / (freq * 360.0)
                array_diff.append((freq, phase, time_ns))
            array_diff = np.array(array_diff, dtype=[('freq', 'i4'), ('phase_deg', 'f4'),
                                                     ('time_ns', 'f4')])
            array_diff_dict['tested'] = array_diff

        # PLOTTING

        numplots = 6
        fig, smpplot = plt.subplots(numplots, sharex=True, figsize=(18, 24))
        xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
        smpplot[numplots - 1].set_xlabel('Frequency (Hz)')
        smpplot[0].set_title(plot_title, fontsize=30)
        smpplot[0].plot(combined_main_array['freq'], combined_main_array['phase_deg'] % 360.0,
                        color=array_colors['main'], label='Main Array Calculated')
        smpplot[1].plot(combined_main_array['freq'], combined_main_array['magnitude'],
                        color=array_colors['main'], label='Main Array Calculated')
        smpplot[0].plot(combined_intf_array['freq'], combined_intf_array['phase_deg'] % 360.0,
                        color=array_colors['intf'], label='Intf Array Calculated')
        smpplot[1].plot(combined_intf_array['freq'], combined_intf_array['magnitude'],
                        color=array_colors['intf'], label='Intf Array Calculated')
        if combined_test_data_flag:
            smpplot[0].plot(combined_array_test['main_combined']['freq'],
                            combined_array_test['main_combined']['phase_deg'] % 360.0,
                            color=array_colors['main_test'], label='Main Array Tested')
            smpplot[1].plot(combined_array_test['main_combined']['freq'],
                            combined_array_test['main_combined']['magnitude'],
                            color=array_colors['main_test'], label='Main Array Tested')
            smpplot[0].plot(combined_array_test['intf_combined']['freq'],
                            combined_array_test['intf_combined']['phase_deg'] % 360.0,
                            color=array_colors['intf_test'], label='Intf Array Tested')
            smpplot[1].plot(combined_array_test['intf_combined']['freq'],
                            combined_array_test['intf_combined']['magnitude'],
                            color=array_colors['intf_test'], label='Intf Array Tested')

        smpplot[0].set_ylabel('Receiver Phasing Matrix Path of\nArrays [degrees]')  # from antenna to feedline end at building.
        smpplot[1].set_ylabel('Combined\nArrays [dB]')  # referenced to power at a single antenna
        smpplot[0].legend(fontsize=12)
        smpplot[1].legend(fontsize=12)

        for plot in range(0, numplots):
            smpplot[plot].grid()
        print "plotting"
        smpplot[2].plot(array_diff_dict['calculated']['freq'], array_diff_dict['calculated']['phase_deg'],
                        label='Calculated Arrays Difference', color=array_colors['main'])
        if combined_test_data_flag:
            smpplot[2].plot(array_diff_dict['tested']['freq'], array_diff_dict['tested']['phase_deg'],
                            label='Tested Arrays Difference', color=array_colors['main_test'])

        smpplot[2].legend(fontsize=12)
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
        # TODO plot time for all paths based on phase. ??

        smpplot[5].plot(array_diff_dict['calculated']['freq'], array_diff_dict['calculated']['time_ns'],
                        label='Calculated Arrays Difference', color=array_colors['main'])
        if combined_test_data_flag:
            smpplot[5].plot(array_diff_dict['tested']['freq'], array_diff_dict['tested']['time_ns'],
                            label='Tested Arrays Difference', color=array_colors['main_test'])
        smpplot[5].set_ylabel('Perceived Time\nDifference b/w arrays\n Based on Phase [ns]')
        smpplot[5].legend(fontsize=12)

        if missing_data:  # not empty
            missing_data_statement = "***MISSING DATA FROM ANTENNA(S) "
            for element in missing_data:
                missing_data_statement = missing_data_statement + element + " "
            print missing_data_statement
            plt.figtext(0.65, 0.06, missing_data_statement, fontsize=15)

        if data_description:
            print data_description
            plt.figtext(0.65, 0.04, data_description, fontsize=8)

        fig.savefig(plot_location + plot_filename)
        plt.close(fig)
    elif combined_test_data_flag:  # only combined data given
        numplots = 4
        fig, smpplot = plt.subplots(numplots, sharex=True, figsize=(9, 12))
        xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
        smpplot[numplots - 1].set_xlabel('Frequency (Hz)')
        smpplot[0].set_title(plot_title, fontsize=30)
        smpplot[0].plot(combined_array_test['main_combined']['freq'],
                        combined_array_test['main_combined']['phase_deg'] % 360,
                        color=array_colors['main_test'], label='Main Array Tested')
        smpplot[1].plot(combined_array_test['main_combined']['freq'],
                        combined_array_test['main_combined']['magnitude'],
                        color=array_colors['main_test'], label='Main Array Tested')
        smpplot[0].plot(combined_array_test['intf_combined']['freq'],
                        combined_array_test['intf_combined']['phase_deg'] % 360,
                        color=array_colors['intf_test'], label='Intf Array Tested')
        smpplot[1].plot(combined_array_test['intf_combined']['freq'],
                        combined_array_test['intf_combined']['magnitude'],
                        color=array_colors['intf_test'], label='Intf Array Tested')

        smpplot[0].set_ylabel('Receiver Phasing Matrix Path of\nArrays [degrees]')  # from antenna to feedline end at building.
        smpplot[1].set_ylabel('Combined\nArrays [dB]')  # referenced to power at a single antenna
        smpplot[0].legend(fontsize=12)
        smpplot[1].legend(fontsize=12)

        array_diff = []
        array_diff_dict = {}
        for m, i in zip(combined_array_test['main_combined'],
                        combined_array_test['intf_combined']):
            freq = i['freq']
            phase = ((m['phase_deg'] - i['phase_deg']) % 360)
            if phase > 180:
                phase = -360 + phase
            time_ns = phase * 10 ** 9 / (freq * 360.0)
            array_diff.append((freq, phase, time_ns))
        array_diff = np.array(array_diff, dtype=[('freq', 'i4'), ('phase_deg', 'f4'),
                                                 ('time_ns', 'f4')])
        array_diff_dict['tested'] = array_diff

        smpplot[2].plot(array_diff_dict['tested']['freq'], array_diff_dict['tested']['phase_deg'],
                        label='Tested Arrays Difference', color=array_colors['main_test'])

        smpplot[2].set_ylabel('Phase Difference\nb/w arrays [deg]')
        smpplot[2].legend(fontsize=12)

        smpplot[3].plot(array_diff_dict['tested']['freq'], array_diff_dict['tested']['time_ns'],
                        label='Tested Arrays Difference', color=array_colors['main_test'])

        smpplot[3].set_ylabel('Perceived Time\nDifference b/w arrays\n Based on Phase [ns]')
        smpplot[3].legend(fontsize=12)

        if missing_data:  # not empty
            missing_data_statement = "***MISSING DATA FROM ANTENNA(S) "
            for element in missing_data:
                missing_data_statement = missing_data_statement + element + " "
            print missing_data_statement
            plt.figtext(0.4, 0.03, missing_data_statement, fontsize=15)

        if data_description:
            print data_description
            plt.figtext(0.4, 0.015, data_description, fontsize=8)

        fig.savefig(plot_location + plot_filename)
        plt.close(fig)

    else:
        sys.exit("Nothing to plot.")

    if combined_test_data_flag:
        if time_file_str != 'None':
            array_diff.tofile(plot_location + time_file_str, sep="\n")
    else:
        if time_file_str != 'None':
            array_diff.tofile(plot_location + time_file_str, sep="\n")

if __name__ == main():
    main()
