#!/usr/bin/python3

# array_feedline_paths.py
# To measure the phase offset in cables, antennas
# using S11 phase measurements and VSWR. Approximate
# S12 phase change at the antenna is found assuming S12 = S21.
# We then plot the estimated phase change at the end of the feedline
# Simply due to feedline and antenna disparities.

import sys
import time
import random
import fnmatch
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import json
import csv

from dataset_operations.dataset_operations import wrap_phase, unwrap_phase, \
    reduce_frequency_array, combine_arrays, reflection_to_transmission_phase, \
    get_min_dataset_length

from retrieve_data.retrieve_data import retrieve_data_from_csv, vswr_to_receive_power, \
    get_cable_loss_array

# General variables to change depending on data being used
radar_name = sys.argv[1]
data_location = sys.argv[2]
plot_location = sys.argv[3]
vswr_files_str = sys.argv[4]
time_file_str = sys.argv[5]
time_file_loc = 'numpy_channel_data/'
path_type = 'antenna-feedline'

plot_filename = radar_name + ' antenna-feedlines-path.png'
plot_title = radar_name + ' Antennas/Feedlines Path'

print(radar_name, data_location, plot_location, vswr_files_str, plot_filename)

sys.path.append(data_location)

# if we assume S12 and S21 are the same (safe for feedlines/antennas only)
# We can assume that S21 phase is S11 phase/2
# We can assume that the transmitted power T12 will be equal to (incident power - cable losses on
# incident)- (S11 (reflected power) + cable losses on reflect)

# estimated cable losses (LMR-400) @ 0.7 db/100ft * 600ft
if 'Saskatoon' in radar_name or 'sas' in radar_name or 'SAS' in radar_name:
    cable_type = 'Belden8237'
    cable_length = 600.0 # ft
elif 'Prince George' in radar_name or 'Prince_George' in radar_name or 'pgr' in radar_name or \
                'PGR' in radar_name:
    cable_type = 'Belden8237' # TODO correct these two values
    cable_length = 600.0 # ft
elif 'Inuvik' in radar_name or 'inv' in radar_name or 'INV' in radar_name:
    cable_type = 'Belden8237' # TODO correct these two values
    cable_length = 600.0 # ft
elif 'Rankin Inlet' in radar_name or 'Rankin_Inlet' in radar_name or 'rkn' in radar_name or \
                'RKN' in radar_name or 'Rankin-Inlet' in radar_name:
    cable_type = 'C1180'
    cable_length = 600.0 # ft TODO verify cable length
elif 'Clyde River' in radar_name or 'Clyde_River' in radar_name or 'cly' in radar_name or \
                'CLY' in radar_name or 'Clyde-River' in radar_name:
    cable_type = 'LMR400'
    cable_length = 600.0 # ft TODO verify cable length
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


def main():

    dtypes_dict = {'freq': 'Freq*', 'vswr': 'VSWR*', 'phase_deg': 'Phase*'}
    all_data_phase_wrapped = {}
    raw_data, colour_dictionary, missing_data, data_description = \
        retrieve_data_from_csv(plot_location + vswr_files_str, data_location, dtypes_dict)

    min_dataset_length = get_min_dataset_length(raw_data)

    # Check and correct frequency array if required.
    reduce_frequency_array(raw_data, min_dataset_length)

    # Get cable loss
    one_array_key = random.choice(list(raw_data.keys()))
    reference_frequency = list(raw_data[one_array_key]['freq'])
    cable_loss_dataset = get_cable_loss_array(reference_frequency, cable_length,
                                              cable_type)

    # get magnitude from VSWR data.
    for antenna, dataset in raw_data.items():
        dataset = vswr_to_receive_power(dataset, cable_loss_dataset)

        # Wrapping then unwrapping ensures there is no 360 degree offset.
        new_dataset = wrap_phase(dataset)
        new_dataset = reflection_to_transmission_phase(new_dataset)
        # now half the phase for single-direction - unwraps within function.

        # Wrapping the new data with new phase for single direction.
        phase_wrapped_data = wrap_phase(new_dataset)
        all_data_phase_wrapped[antenna] = phase_wrapped_data


    all_data = {}
    # Also get data that is not phase_wrapped for calculation purposes.
    for ant, dataset in all_data_phase_wrapped.items():
        all_data[ant] = unwrap_phase(dataset)

    ######################################################################################
    # Getting the line of best fit for each antenna and the combined arrays.
    # Getting the offset from the line of best fit for each antenna and array.
    linear_fit_dict = {}
    for ant, dataset in all_data.items():
        slope, intercept, rvalue, pvalue, stderr = stats.linregress(dataset['freq'],
                                                                    dataset['phase_rad'])
        linear_fit_dict[ant] = {'slope': slope, 'intercept': intercept, 'rvalue': rvalue,
                                'pvalue': pvalue, 'stderr': stderr}
        offset_of_best_fit = []
        best_fit_line = []
        for entry in dataset:
            best_fit_value = slope * entry['freq'] + intercept
            offset_of_best_fit.append(entry['phase_rad'] - best_fit_value)
            best_fit_line.append(best_fit_value)
        best_fit_line = np.array(best_fit_line, dtype=[('phase_rad', 'f4')])
        best_fit_line = wrap_phase(best_fit_line)
        offset_of_best_fit = np.array(offset_of_best_fit, dtype=[('phase_rad', 'f4')])
        offset_of_best_fit = wrap_phase(offset_of_best_fit)
        linear_fit_dict[ant]['offset_of_best_fit_rads'] = offset_of_best_fit['phase_rad']
        linear_fit_dict[ant]['time_delay_ns'] = round(slope / (2 * math.pi), 11) * -10 ** 9
        linear_fit_dict[ant]['best_fit_line_rads'] = best_fit_line
        linear_fit_dict[ant]['best_fit_line_rads'] = wrap_phase(linear_fit_dict[ant][
                                                               'best_fit_line_rads'])


    # Get all main and interferometer keys
    main_data = {}
    intf_data = {}
    for ant in all_data.keys():
        if ant[0] == 'M':
            main_data[ant] = all_data[ant]
        elif ant[0] == 'I':
            intf_data[ant] = all_data[ant]

    # Combine_arrays returns unwrapped dataset.
    unwrapped_main_array = combine_arrays(main_data)
    unwrapped_intf_array = combine_arrays(intf_data)

    # Wrapping after unwrapping ensures the first values in array are within -pi to pi.
    combined_main_array = wrap_phase(unwrapped_main_array)
    combined_intf_array = wrap_phase(unwrapped_intf_array)

    # combined main array slope
    slope, intercept, rvalue, pvalue, stderr = stats.linregress(unwrapped_main_array[
                                                                    'freq'],
                                                                unwrapped_main_array[
                                                                    'phase_rad'])
    offset_of_best_fit = []
    best_fit_line = []
    for entry in unwrapped_main_array:
        best_fit_value = slope * entry['freq'] + intercept
        offset_of_best_fit.append(entry['phase_rad'] - best_fit_value)
        best_fit_line.append(best_fit_value)
    best_fit_line = np.array(best_fit_line, dtype=[('phase_rad', 'f4')])
    best_fit_line = wrap_phase(best_fit_line)
    offset_of_best_fit = np.array(offset_of_best_fit, dtype=[('phase_rad', 'f4')])
    offset_of_best_fit = wrap_phase(offset_of_best_fit)
    linear_fit_dict['M_all'] = {'slope': slope, 'intercept': intercept, 'rvalue': rvalue,
                                'pvalue': pvalue, 'stderr': stderr,
                                'offset_of_best_fit_rads': offset_of_best_fit[
                                    'phase_rad'],
                                'time_delay_ns': round(slope / (2 * math.pi), 11) * -10
                                                                                     ** 9,
                                'best_fit_line_rads': best_fit_line}

    # combined intf array slope
    slope, intercept, rvalue, pvalue, stderr = stats.linregress(unwrapped_intf_array[
                                                                    'freq'],
                                                                unwrapped_intf_array[
                                                                    'phase_rad'])
    offset_of_best_fit = []
    best_fit_line = []
    for entry in unwrapped_intf_array:
        best_fit_value = slope * entry['freq'] + intercept
        offset_of_best_fit.append(entry['phase_rad'] - best_fit_value)
        best_fit_line.append(best_fit_value)
    best_fit_line = np.array(best_fit_line, dtype=[('phase_rad', 'f4')])
    best_fit_line = wrap_phase(best_fit_line)
    offset_of_best_fit = np.array(offset_of_best_fit, dtype=[('phase_rad', 'f4')])
    offset_of_best_fit = wrap_phase(offset_of_best_fit)
    linear_fit_dict['I_all'] = {'slope': slope, 'intercept': intercept, 'rvalue': rvalue,
                                'pvalue': pvalue, 'stderr': stderr,
                                'offset_of_best_fit_rads': offset_of_best_fit[
                                    'phase_rad'],
                                'time_delay_ns': round(slope / (2 * math.pi), 11) * -10
                                                                                     ** 9,
                                'best_fit_line_rads': best_fit_line}

    ######################################################################################
    # Computing the phase difference between the arrays and
    # also getting tdiff across the frequency range.
    array_diff_raw = []
    for m, i in zip(unwrapped_main_array, unwrapped_intf_array):
        freq = i['freq']
        phase = (m['phase_deg'] - i['phase_deg'])
        array_diff_raw.append((freq, phase, 0.0))
    array_diff_raw = np.array(array_diff_raw, dtype=[('freq', 'i4'), ('phase_deg', 'f4'),
                                             ('time_ns', 'f4')])

    array_diff = wrap_phase(array_diff_raw)

    # Now insert the tdiff in ns after the phase has been wrapped.
    for dp in array_diff:
        freq = dp['freq']
        phase = dp['phase_deg']
        time_ns = phase * 10**9 / (freq * 360.0)
        dp['time_ns'] = time_ns


    ######################################################################################
    # Writing the array difference and combined arrays to file
    if time_file_str != 'None':
        array_diff.tofile(plot_location + path_type + time_file_str, sep="\n")
    if time_file_loc != 'None':
        for ant, array in all_data.items():
            array.tofile(plot_location + time_file_loc + path_type + ant + '.txt', sep="\n")
        unwrapped_main_array.tofile(plot_location + time_file_loc + path_type +
                            'main_array_combined.txt', sep="\n")
        unwrapped_intf_array.tofile(plot_location + time_file_loc + path_type +
                            'intf_array_combined.txt', sep="\n")

    ######################################################################################
    # PLOTTING
    numplots = 7
    plot_num = 0
    fig, smpplot = plt.subplots(numplots, 1, sharex='all', figsize=(18, 24),
                                gridspec_kw={'height_ratios': [2, 2, 1, 1, 1, 1, 1]})
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[numplots - 1].set_xlabel('Frequency (Hz)', size=25.0)
    print("plotting")


    # PLOT: combined arrays dB and phase.
    smpplot[plot_num].set_title(plot_title, size=48.0)
    smpplot[plot_num].plot(combined_main_array['freq'], combined_main_array['phase_deg'],
                    color='#2942a8', label='Main Array')

    smpplot[plot_num].plot(combined_intf_array['freq'], combined_intf_array['phase_deg'],
                    color='#8ba1fa', label='Intf Array')

    db_smpplot = smpplot[0].twinx()

    db_smpplot.plot(combined_main_array['freq'], combined_main_array['magnitude'],
                    color='#bd3f3f', label='Main Array')
    db_smpplot.plot(combined_intf_array['freq'], combined_intf_array['magnitude'],
                    color='#f99191', label='Intf Array')

    smpplot[plot_num].set_ylabel('Incoming Feedline Array\nPhase [degrees]', color='#3352cd',
                          size=25.0)
    # blue
    smpplot[plot_num].tick_params(axis='y', labelcolor='#3352cd')

    # from antenna to feedline end at building.
    db_smpplot.set_ylabel('Combined\nArray [dB]', color='#de4b4b', size=25.0)  # red
    db_smpplot.tick_params(axis='y', labelcolor='#de4b4b')
    # referenced to power at a single antenna
    plot_num += 1

    # PLOT: Time difference between arrays single direction TODO this is not 1 direction
    smpplot[plot_num].set_ylabel('S12 Perceived Time\nDifference b/w arrays\n Based on Phase ['
                          'ns]', size=25.0)
    smpplot[plot_num].plot(array_diff['freq'], array_diff['time_ns'])
    plot_num += 1

    # PLOT: Main Array Offset from their Best Fit Lines, and Intf Array
    for ant, dataset in all_data.items():
        if ant[0] == 'M':  # plot with main array
            smpplot[plot_num].plot(dataset['freq'], linear_fit_dict[ant][
                'offset_of_best_fit_rads'] * 180.0 / math.pi,
                            label='{}, delay={} ns'.format(ant,
                                                           linear_fit_dict[ant]['time_delay_ns']),
                            color=hex_dictionary[ant])
        elif ant[0] == 'I':
            smpplot[plot_num + 1].plot(dataset['freq'], linear_fit_dict[ant][
                'offset_of_best_fit_rads'] * 180.0 / math.pi,
                    label='{}, delay={} ns'.format(ant, linear_fit_dict[ant][
                        'time_delay_ns']), color=hex_dictionary[ant])

    smpplot[plot_num].plot(all_data['M0']['freq'], linear_fit_dict['M_all'][
        'offset_of_best_fit_rads'] * 180.0 / math.pi, color=hex_dictionary['other'],
            label='Combined Main, delay={} ns'.format(linear_fit_dict[
                'M_all']['time_delay_ns']))  # plot last
    smpplot[plot_num + 1].plot(all_data['M0']['freq'], linear_fit_dict['I_all'][
        'offset_of_best_fit_rads'] * 180.0 / math.pi, color=hex_dictionary['other'],
            label='Combined Intf, delay={} ns'.format(linear_fit_dict[
                'I_all']['time_delay_ns']))  # plot last


    smpplot[plot_num].legend(fontsize=10, ncol=4)
    smpplot[plot_num + 1].legend(fontsize=12)
    smpplot[plot_num].set_ylabel('S12 Main Phase Offset\n from Own Line of Best\nFit [degrees]')
    smpplot[plot_num + 1].set_ylabel('S12 Intf Phase Offset\n from Own Line of Best\nFit [degrees]')
    plot_num += 2

    # PLOT: Phase wrapped of all data
    for ant, dataset in all_data_phase_wrapped.items():
        smpplot[plot_num].plot(dataset['freq'], dataset['phase_deg'], label=ant,
                        color=hex_dictionary[ant])

    if missing_data:  # not empty
        missing_data_statement = "***MISSING DATA FROM ANTENNA(S) "
        for element in missing_data:
            missing_data_statement = missing_data_statement + element + " "
        print(missing_data_statement)
        plt.figtext(0.65, 0.05, missing_data_statement, fontsize=15)

    if data_description:
        print(data_description)
        plt.figtext(0.65, 0.10, data_description, fontsize=15)

    for plot in range(0, numplots):
        smpplot[plot].grid()

    fig.savefig(plot_location + plot_filename)
    plt.close(fig)


if __name__ == main():
    main()
