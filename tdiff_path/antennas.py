#!/usr/bin/python3

# array_feedline_paths.py
# To estimate the antenna response by removing an estimated cable response
# using SWR measurements. This script is for when you have magnitude, not
# VSWR dataset.

import sys
import time
import fnmatch
import random
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats, constants
import json
import csv

from dataset_operations.dataset_operations import wrap_phase, unwrap_phase, \
    reduce_frequency_array, combine_arrays, reflection_to_transmission_phase

# General variables to change depending on data being used
radar_name = sys.argv[1]
data_location = sys.argv[2]
plot_location = sys.argv[3]
vswr_files_str = sys.argv[4]
time_file_str = sys.argv[5]

plot_filename = radar_name + ' antennas-path.png'
plot_title = radar_name + ' Antennas Path'

print(radar_name, data_location, plot_location, vswr_files_str, plot_filename)

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
    #cable_loss = 3.0  # in dB
    cable_length = 600  # in ft
    cable_type = 'RG8'
elif 'Prince George' in radar_name or 'Prince_George' in radar_name or 'pgr' in radar_name or \
                'PGR' in radar_name:
    #cable_loss = 3.0  # in dB
    cable_length = 600  # in ft
    cable_type = 'RG8'
elif 'Inuvik' in radar_name or 'inv' in radar_name or 'INV' in radar_name:
    #cable_loss = 2.5  # in dB
    cable_length = 600  # in ft
    cable_type = 'LMR400' # TODO check this
elif 'Rankin Inlet' in radar_name or 'Rankin_Inlet' in radar_name or 'rkn' in radar_name or \
                'RKN' in radar_name or 'Rankin-Inlet' in radar_name:
    #cable_loss = 2.0  # in dB
    cable_length = 600  # in ft
    cable_type = 'LMR400' # TODO check this
elif 'Clyde River' in radar_name or 'Clyde_River' in radar_name or 'cly' in radar_name or \
                'CLY' in radar_name or 'Clyde-River' in radar_name:
    #cable_loss = 2.5  # in dB
    cable_length = 600  # in ft
    cable_type = 'LMR400'
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


def cable_loss(cable_length, cable_type):
    """
    Return the cable loss model of the given cable_type for the given cable_length.
    :param cable_length: 
    :param cable_type: 
    :return: 
    """


def main():
    data_description = []
    missing_data = []
    all_data = {}
    all_data_phase_wrapped = {}
    reflection_dict = {}
    min_dataset_length = 100000  # just a big number
    for k, v in vswr_files.items():
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

                data.append((freq, VSWR, phase, 0.0))

            data = np.array(data, dtype=[('freq', 'i4'), ('vswr-raw', 'f4'),
                                         ('phase_deg', 'f4'),
                                         ('vswr-at-balun', 'f4')])

            phase_wrapped_data = wrap_phase(data)

            #print data[-1]

            if len(data) < min_dataset_length:
                min_dataset_length = len(data)

            if k[0] == 'M' or k[0] == 'I':  # in main files.
                all_data_phase_wrapped[k] = phase_wrapped_data
            else:
                sys.exit('There is an invalid key {}'.format(k))

            hex_dictionary[k] = hex_colors[0]
            hex_colors.remove(hex_dictionary[k])

    reduce_frequency_array(all_data_phase_wrapped, min_dataset_length)

    # Wrapping then unwrapping ensures there is no 360 degree offset.
    for ant, dataset in all_data_phase_wrapped.items():
        all_data[ant] = unwrap_phase(dataset)

    # create cable loss array based on frequency array TODO





    # WORKING HERE THE REST NEEDS TO BE LOOKED AT



    reflection_dict, freq_array = correct_frequency_array(reflection_dict)

    reflection_data = []
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
        power_reaching_balun_w = 10 ** (-1 * cable_loss / 10)
        # get single-direction data by making the power base = power_reaching_balun_w
        # (incident at mismatch point at balun).

        dB_reflected_at_balun = -1 * return_loss_dB + cable_loss

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
        reflection_data.append((freq, receive_power, float(phase), 0.0))
    reflection_data = np.array(reflection_data,
                               dtype=[('freq', 'i4'), ('receive_power', 'f4'),
                                      ('phase_deg', 'f4')])

    reflection_data = wrap_phase(reflection_data)
    unwrapped_reflection_data = unwrap_phase(reflection_data)

    for entry in unwrapped_reflection_data:
        data.append((entry['freq'], entry['phase_deg'] / 2.0))

    data = np.array(data, dtype=[('freq', 'i4'), ('phase_deg', 'f4')])

    if len(data) < min_dataset_length:
        min_dataset_length = len(data)


    #print(reflection_dict['I0'][-1])

    # Get expected phase of feedline, assuming 600 ft.
    feedline_distance_ft = 217 * 3.28 * 0.66 + 50.0
    velocity_factor_feedline = 0.66
    time_ns = feedline_distance_ft/(3.28 * constants.speed_of_light * velocity_factor_feedline)  #66% propagation in RG8, .82 in rg-8x
    # estimate phase offset through the feedline in one direction.

    # subtract the line with the slope of the feedline.
    # intercept will equal intercept of

    antenna_data = {}

    first_freq = freq_array[0]
    freq_diff = freq_array - first_freq
    feedline_phase_estimate_array = 2 * 180.0 * -time_ns * freq_diff

    # for path, data_array in all_data.items():
    #     phase_list = []
    #     for entry in data_array:
    #         phase_list.append(entry['phase_deg'])
    #     phase_array = np.array(phase_list)
    #     intercept = phase_array[0]
    #     #feedline_phase_estimate_array_this_path = feedline_phase_estimate_array + intercept
    #     new_array = np.subtract(phase_array, feedline_phase_estimate_array)
    #     antenna_data[path] = new_array
    #
    # all_data_array = np.concatenate((['Freq'],freq_array))
    #
    # for path, data_array in antenna_data.items():
    #     print type(data_array)
    #     phase_array = np.concatenate(([path], data_array))
    #     all_data_array = np.concatenate((all_data_array, phase_array), axis=1)
    #
    # if time_file_str != 'None':
    #     all_data_array.tofile(plot_location + time_file_str, sep=",")

    for path, data_array in reflection_dict.items():
        phase_list = []
        for entry in data_array:
            phase_list.append(entry['phase_deg_unwrap'])
        phase_array = np.array(phase_list)
        #intercept = phase_array[0]
        feedline_phase_estimate_array_reflection = 2 * feedline_phase_estimate_array
        new_array = np.subtract(phase_array, feedline_phase_estimate_array_reflection)
        antenna_data[path] = new_array

    all_data_array = np.concatenate((['Freq'],freq_array))

    for path, data_array in antenna_data.items():
        phase_array = np.concatenate(([path], data_array))
        all_data_array = np.concatenate((all_data_array, phase_array), axis=1)

    if time_file_str != 'None':
        all_data_array.tofile(plot_location + time_file_str, sep=",")

    # PLOTTING

    numplots = 3
    fig, smpplot = plt.subplots(numplots, sharex=True, figsize=(18, 18))
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[numplots -1].set_xlabel('Frequency (Hz)')
    smpplot[0].set_title(plot_title)

    smpplot[0].set_ylabel('Phase Estimate of\nAntennas [degrees]')  # from antenna to feedline end at building.

    for ant, dataset in antenna_data.items():
        smpplot[0].plot(freq_array, dataset, label='{}'.format(ant),
                        color=hex_dictionary[ant])

    smpplot[0].legend(fontsize=10, ncol=4)

    smpplot[1].set_ylabel('Phase Estimate of Feedline [degrees]\nFeedline Length = {} ft,\nFeedline'
                          ' Velocity Factor = {}'.format(feedline_distance_ft,
                                                         velocity_factor_feedline))  # from antenna to feedline end at building.

    smpplot[1].plot(freq_array, feedline_phase_estimate_array)

    smpplot[2].set_ylabel('Reflection Phase Offset of\nAntenna + Feedline [degrees]')  # from antenna to feedline end at building.

    for ant, dataset in reflection_dict.items():
        smpplot[2].plot(freq_array, dataset['phase_deg_unwrap'], label='{}'.format(ant),
                        color=hex_dictionary[ant])

    smpplot[2].legend(fontsize=10, ncol=4)


    for plot in range(numplots):
        smpplot[plot].grid()
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
