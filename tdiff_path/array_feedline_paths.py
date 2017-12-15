#!/usr/bin/python

# array_feedline_paths.py
# To measure the phase offset in cables, antennas
# using S11 phase measurements and VSWR. Approximate
# S12 phase change at the antenna is found assuming S12 = S21.
# We then plot the estimated phase change at the end of the feedline
# Simply due to feedline and antenna disparities.

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
vswr_files_str = sys.argv[4]
time_file_str = sys.argv[5]

plot_filename = radar_name + ' antenna-feedlines-path.png'
plot_title = radar_name + ' Antennas/Feedlines Path'

print radar_name, data_location, plot_location, vswr_files_str, plot_filename

sys.path.append(data_location)

with open(plot_location + vswr_files_str) as f:
    vswr_files = json.load(f)

#
#
# A list of 21 colors that will be assigned to antennas to keep plot colors consistent.
hex_colors = ['#ff1a1a', '#993300', '#ffff1a', '#666600', '#ff531a', '#cc9900', '#99cc00',
              '#7a7a52', '#004d00', '#33ff33', '#26734d', '#003366', '#33cccc', '#00004d',
              '#5500ff', '#a366ff', '#ff00ff', '#e6005c', '#ffaa80', '#999999']
hex_dictionary = {'other': '#000000'}

# if we assume S12 and S21 are the same (safe for feedlines/antennas only)
# We can assume that S21 phase is S11 phase/2
# We can assume that the transmitted power T12 will be equal to (incident power - cable losses on
# incident)- (S11 (reflected power) + cable losses on reflect)

# estimated cable losses (LMR-400) @ 0.7 db/100ft * 600ft
if 'Saskatoon' in radar_name or 'sas' in radar_name or 'SAS' in radar_name:
    cable_loss = 3.6  # in dB Belden 8237 - 0.6 dB/100ft
elif 'Prince George' in radar_name or 'Prince_George' in radar_name or 'pgr' in radar_name or \
                'PGR' in radar_name:
    cable_loss = 3.0  # in dB
elif 'Inuvik' in radar_name or 'inv' in radar_name or 'INV' in radar_name:
    cable_loss = 2.5  # in dB
elif 'Rankin Inlet' in radar_name or 'Rankin_Inlet' in radar_name or 'rkn' in radar_name or \
                'RKN' in radar_name:
    cable_loss = 2.0  # in dB
elif 'Clyde River' in radar_name or 'Clyde_River' in radar_name or 'cly' in radar_name or \
                'CLY' in radar_name:
    cable_loss = 2.5  # in dB
else:
    sys.exit('Not a valid radar name.')

# receive power will be calculated from transmit power losses.
# transmit S21 = (incident-cable losses)-(S11+cable losses)
# S11=current return loss referenced to incident = 0dB.
# make incident at port 2 = 0 dB = incident-cable losses = -cable_loss = 0
# if we make the power at antenna = 1, and S12 = S21
# receive S12 = incident-reflected_loss_at_balun-cable_loss
# we will calculate reflected loss at balun using our measured reflected loss at instrument,
# remembering that has cable loss included and was going in two directions.

# amplitudes calculated as if all antennas receive the same signal strength at the antenna.
# Balun mismatch for each individual antenna is estimated here.


def unwrap_phase(data):
    # take a numpy array with phase_deg and phase_rad datatypes and unwrap.
    if max(data['phase_deg']) < 180.0 and min(data['phase_deg']) > -180.0:
        # unwrap
        for num, entry in enumerate(data['phase_deg']):
            if entry > 320.0 + data['phase_deg'][num - 1]:
                for i in range(num, len(data)):
                    data['phase_deg'][i] = data['phase_deg'][i] - 360.0
                    if 'phase_rad' in data.dtype.names:
                        data['phase_rad'][i] = data['phase_deg'][i] * math.pi / 180.0
            elif entry < -320.0 + data['phase_deg'][num - 1]:
                for i in range(num, len(data)):
                    data['phase_deg'][i] = data['phase_deg'][i] + 360.0
                    if 'phase_rad' in data.dtype.names:
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
            amplitude_1 = 10 ** (c['receive_power'] / 20)
            amplitude_2 = 10 ** (a['receive_power'] / 20)

            combined_amp_squared = (
                amplitude_1 ** 2 + amplitude_2 ** 2 + 2 * amplitude_1 * amplitude_2 * math.cos(
                    phase_rads1 - phase_rads2))
            combined_amp = math.sqrt(combined_amp_squared)
            # we based it on amplitude of 1 at each antenna.
            c['receive_power'] = 20 * math.log(combined_amp, 10)
            combined_phase = math.atan2(
                amplitude_1 * math.sin(phase_rads1) + amplitude_2 * math.sin(phase_rads2),
                amplitude_1 * math.cos(phase_rads1) + amplitude_2 * math.cos(phase_rads2))

            # this is negative so make it positive cos(x-theta)
            c['phase_rad'] = -combined_phase
            c['phase_deg'] = -combined_phase * 360.0 / (2.0 * math.pi)

    unwrap_phase(combined_array)
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
    missing_data = []
    main_data = {}
    intf_data = {}
    min_dataset_length = 100000  # just a big number
    for k, v in vswr_files.iteritems():
        if k == '_comment':
            data_description = v
            continue
        if v == 'dne':
            missing_data.append(k)
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
                vswr_header = 'VSWR*'
                vswr_columns = [i for i in range(len(row)) if
                                fnmatch.fnmatch(row[i], vswr_header)]
                freq_column = freq_columns[0]
                vswr_column = vswr_columns[0]
                phase_header = 'Phase*'
                phase_columns = [i for i in range(len(row)) if
                                fnmatch.fnmatch(row[i], phase_header)]
                phase_column = phase_columns[0]
                if (abs(vswr_column - freq_column) > 2) or (
                            abs(phase_column - freq_column) > 2):
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
                    VSWR = float(row[vswr_column])
                    phase = float(row[phase_column])
                except:
                    continue

                return_loss_dB = 20 * math.log(((VSWR + 1) / (VSWR - 1)), 10)
                # return loss reaching instrument.
                # calculate mismatch error. need to adjust power base to power at antenna mismatch.
                # ratio to 1, approaching the balun point.
                power_reaching_balun_w = 10 ** (-1*cable_loss / 10)
                # get single-direction data by making the power base = power_reaching_balun_w
                # (incident at mismatch point at balun).

                dB_reflected_at_balun = -1*return_loss_dB + cable_loss

                w_reflected_at_balun = 10 ** (dB_reflected_at_balun / 10)

                w_transmitted_at_balun = power_reaching_balun_w - w_reflected_at_balun
                # print "transmitted w at balun is {}".format(w_transmitted_at_balun)
                if w_transmitted_at_balun <= 0:
                    print radar_name, vswr_files_str
                    print "Antenna: {}".format(k)
                    print freq
                    print "WRONG"
                    print "This would suggest your cable loss model is too lossy."
                    print "Cable loss = {} db".format(cable_loss)
                    sys.exit()
                reflection_dB_at_balun = 10 * math.log((w_reflected_at_balun /
                                                        power_reaching_balun_w), 10)
                transmission_dB_at_balun = 10 * math.log(w_transmitted_at_balun /
                                                         power_reaching_balun_w, 10)

                # ASSUMING we have a symmetrical mismatch point at the balun and transmission
                # S12 = S21.
                # power incoming from antenna will have mismatch point and then cable losses.
                receive_power = transmission_dB_at_balun - cable_loss
                receive_power = round(receive_power, 5)
                phase_rad = (float(phase)/2) * math.pi / 180.0
                data.append((freq, receive_power, float(phase) / 2, phase_rad))
            data = np.array(data, dtype=[('freq', 'i4'), ('receive_power', 'f4'),
                                         ('phase_deg', 'f4'), ('phase_rad', 'f4')])

            unwrap_phase(data)

            if len(data) < min_dataset_length:
                min_dataset_length = len(data)

            if k[0] == 'M':  # in main files.
                main_data[k] = data
            elif k[0] == 'I':  # in intf files
                intf_data[k] = data
            else:
                sys.exit('There is an invalid key {}'.format(k))

            hex_dictionary[k] = hex_colors[0]
            hex_colors.remove(hex_dictionary[k])

    check_frequency_array(main_data, min_dataset_length)
    check_frequency_array(intf_data, min_dataset_length)

    all_data = main_data.copy()
    all_data.update(intf_data)

    # for each antenna, get the linear fit and plot the offset from linear fit.
    linear_fit_dict = {}
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

    combined_main_array = combine_arrays(main_data)
    combined_intf_array = combine_arrays(intf_data)

    # combined main array slope
    slope, intercept, rvalue, pvalue, stderr = stats.linregress(combined_main_array['freq'],
                                                                combined_main_array['phase_rad'])
    offset_of_best_fit = []
    for entry in combined_main_array:
        best_fit_value = slope * entry['freq'] + intercept
        offset_of_best_fit.append(entry['phase_rad'] - best_fit_value)
    linear_fit_dict['M_all'] = {'slope': slope, 'intercept': intercept, 'rvalue': rvalue,
                                'pvalue': pvalue, 'stderr': stderr,
                                'offset_of_best_fit': np.array(offset_of_best_fit),
                                'time_delay_ns': round(slope / (2 * math.pi), 11) * -10 ** 9}

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

    # dx is constant
    # delay_dict = {}
    # dx = 2.0 * math.pi * (all_data['M0']['freq'][-1] - all_data['M0']['freq'][0]) / min_dataset_length
    # #delay_freq_list = [all_data['M0']['freq'][i] + (dx / (4.0 * math.pi)) for i in range(0, len(all_data['M0']['freq']) - 1)]
    # delay_freq_list = list(all_data['M0']['freq'])
    # print 'dx = {}'.format(dx)
    # for ant, dataset in all_data.items():
    #     #dy = np.diff(dataset['phase_rad']) * -10 ** 9 / dx
    #     # np.insert(dy, [0], delay_freq_list, axis=1)
    #
    #     # for smoother plot
    #     dy = get_slope_of_phase_in_nano(dataset['phase_rad'], delay_freq_list)
    #     delay_dict[ant] = dy
    # delay_dict['M_all'] = get_slope_of_phase_in_nano(combined_main_array['phase_rad'], delay_freq_list)
    # delay_dict['I_all'] = get_slope_of_phase_in_nano(combined_intf_array['phase_rad'], delay_freq_list)

    array_diff = []
    for m, i in zip(combined_main_array, combined_intf_array):
        freq = i['freq']
        phase = ((m['phase_deg'] - i['phase_deg']) % 360.0)
        if phase > 180:
            phase = -360 + phase
        time_ns = phase * 10**9 / (freq * 360.0)
        array_diff.append((freq, phase, time_ns))
    array_diff = np.array(array_diff, dtype=[('freq', 'i4'), ('phase_deg', 'f4'),
                                             ('time_ns', 'f4')])

    unwrap_phase(array_diff)

    if time_file_str != 'None':
        array_diff.tofile(plot_location + time_file_str, sep="\n")
    # PLOTTING

    numplots = 6
    fig, smpplot = plt.subplots(numplots, sharex=True, figsize=(18, 24))
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[numplots - 1].set_xlabel('Frequency (Hz)')
    smpplot[0].set_title(plot_title)
    smpplot[0].plot(combined_main_array['freq'], combined_main_array['phase_deg'] % 360.0,
                    color=hex_dictionary['M0'], label='Main Array')
    smpplot[1].plot(combined_main_array['freq'], combined_main_array['receive_power'],
                    color=hex_dictionary['M0'], label='Main Array')
    smpplot[0].plot(combined_intf_array['freq'], combined_intf_array['phase_deg'] % 360.0,
                    color=hex_dictionary['I0'], label='Intf Array')
    smpplot[1].plot(combined_intf_array['freq'], combined_intf_array['receive_power'],
                    color=hex_dictionary['I0'], label='Intf Array')

    smpplot[0].set_ylabel('S12 Phase of\nArrays [degrees]')  # from antenna to feedline end at building.
    smpplot[1].set_ylabel('Combined\nArray [dB]')  # referenced to power at a single antenna

    for plot in range(0, numplots):
        smpplot[plot].grid()
    print "plotting"
    smpplot[2].plot(array_diff['freq'], array_diff['phase_deg'])
    smpplot[2].set_ylabel('S12 Phase\nDifference Between\nArrays [degrees]')

    for ant, dataset in all_data.items():
        if ant[0] == 'M': # plot with main array
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
    smpplot[3].set_ylabel('S12 Main Phase Offset\n from Own Line of Best\nFit [degrees]')
    smpplot[4].set_ylabel('S12 Intf Phase Offset\n from Own Line of Best\nFit [degrees]')
    smpplot[5].set_ylabel('S12 Perceived Time\nDifference b/w arrays\n Based on Phase [ns]')
    smpplot[5].plot(array_diff['freq'], array_diff['time_ns'])

    # smpplot[5].set_ylabel('Main Array Path Delays (ns)')
    # smpplot[6].set_ylabel('Intf Array Path Delays (ns)')
    # for ant, dataset in delay_dict.items():
    #     #print len(delay_freq_list), dataset.shape
    #     if ant[0] == 'M':
    #         if ant != 'M_all':
    #             smpplot[5].plot(delay_freq_list, dataset, color=hex_dictionary[ant],
    #                             label='{}'.format(ant))
    #     else:
    #         if ant != 'I_all':
    #             smpplot[6].plot(delay_freq_list, dataset, color=hex_dictionary[ant],
    #                             label='{}'.format(ant))
    #
    # smpplot[5].plot(delay_freq_list, delay_dict['M_all'], color=hex_dictionary['other'],
    #                             label='Combined Main')  # plot last
    # smpplot[6].plot(delay_freq_list, delay_dict['I_all'], color=hex_dictionary['other'],
    #                 label='Combined Intf')
    # xmin, xmax, ymin, ymax = smpplot[5].axis()
    # if ymax > 1500:
    #     smpplot[5].axis(ymax=1500)
    # if ymin < 0:
    #     smpplot[5].axis(ymin=0)
    # xmin, xmax, ymin, ymax = smpplot[6].axis()
    # if ymax > 1500:
    #     smpplot[6].axis(ymax=1500)
    # if ymin < 0:
    #     smpplot[6].axis(ymin=0)

    #smpplot[5].legend(fontsize=10, ncol=3)
    #smpplot[6].legend(fontsize=12)

    #smpplot[7].plot(delay_freq_list, delay_dict['M_all'] - delay_dict['I_all'])
    #smpplot[7].set_ylabel('Time diff b/w arrival\nof Arrays from\nFeedlines Alone (ns)')
    #xmin, xmax, ymin, ymax = smpplot[7].axis()
    #if ymax > 1000 or ymin < -1000:
    #    smpplot[7].axis(ymin=-1000, ymax=1000)

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