#!/usr/bin/python3

# array_feedline_paths.py
# Plot the VSWR information for feedlines and antennas and
# use this information to estimate a phase delay value for the
# antenna and feedline path in a single direction.
# Approximate S12 phase change at the antenna is found assuming S12 = S21.

import sys
import argparse
import random
import math
import numpy as np
import matplotlib.pyplot as plt

import dataset_operations.dataset_operations as do
import retrieve_data.retrieve_data as retrieve


def usage_msg():
    """
    Return the usage message for this script.

    This is used if a -h flag or invalid arguments are provided.

    :return: the usage message
    """

    usage_message = """ array_feedline_paths.py [-h] radar_name data_location
    plot_location vswr_files_str time_file_str

    This script is intended for use with VSWR data of some length of feedline leading
    up to the SuperDARN antenna. A single direction phase path (S12) is estimated from
    the return path of the VSWR data (S11). This is used to determine the phase delay
    from the signal incident at the antenna to the end of the feedline. This data can be
    combined with other phase path data to estimate the entire path's phase delay.

    Data provided to this script should include 'VSWR', 'Phase', and 'Freq'. This
    script is set up to retrieve this data from csv's produced by ZVHView after being
    recorded by a Rohde & Schwarz ZVH4.
    """

    return usage_message


def script_parser():
    """
    Creates the parser to retrieve the arguments.

    :return: parser, the argument parser for this script.
    """

    radar_name_help = "Name of the radar, appears in plot title and filename. Limited " +\
                      "to  Canadian SuperDARN radars at this time in order to give " +\
                      "accurate cable loss models. "

    data_location_help = "Path location of the data files. Data filenames are provided" +\
                         "in the vswr_files_str. "

    plot_location_help = "Path location of where to place the plots produced in this " +\
                         "script."

    vswr_files_str_help = "The name of a json file that is mapping the path names to " +\
        " the data filename for that path. All path names should begin" +\
        "with an 'M' or 'I' to signify main or interferometer array. " +\
        "There can also be a _comment key to leave a data_description " +\
        "string on the plot. This file should be in the plot_location " +\
        "path. All data files referenced in this file should be " +\
        "located in the data_location path. "

    time_file_str_help = "The name of the file in which to record the difference " +\
                         "between main and interferometer arrays. This would be a " +\
                         "numpy array write to file with dtypes 'freq', 'phase_deg', " +\
                         "and 'time_ns'. This file would be written in the " +\
                         "plot_location, under a sub-directory numpy_channel_data."

    parser = argparse.ArgumentParser(usage=usage_msg())
    parser.add_argument("radar_name", help=radar_name_help)
    parser.add_argument("data_location", help=data_location_help)
    parser.add_argument("plot_location", help=plot_location_help)
    parser.add_argument("vswr_files_str", help=vswr_files_str_help)
    parser.add_argument(
        "-tdiff",
        "--record-tdiff",
        nargs='?',
        const='delays.txt',
        default=None,
        help=time_file_str_help)

    return parser


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

    parser = script_parser()
    args = parser.parse_args()

    # Get the args so we can retrieve the data and plot in the correct
    # location.
    radar_name = args.radar_name
    data_location = args.data_location
    plot_location = args.plot_location
    vswr_files_str = args.vswr_files_str
    time_file_str = args.record_tdiff
    time_file_loc = 'numpy_channel_data/'
    path_type = 'antenna-feedline'

    plot_filename = radar_name + '-antenna-feedlines-path.png'
    plot_title = radar_name + ' Antennas/Feedlines Path'

    print(
        '\nPlotting for {radar_name}\nUsing data from {data_location}\n'
        'Plots will be placed in {plot_location}\n'
        'Plot name is {plot_filename}\n'
        'Data used from mapping in {vswr_files_str}\n'.format(
            radar_name=radar_name,
            data_location=data_location,
            plot_location=plot_location,
            plot_filename=plot_filename,
            vswr_files_str=vswr_files_str))

    sys.path.append(data_location)

    #
    # Get the cable model depending on the site being analyzed.
    if 'Saskatoon' in radar_name or 'sas' in radar_name or 'SAS' in radar_name:
        cable_type = 'Belden8237'  # known
        cable_length = 600.0  # ft ??
    elif 'Prince George' in radar_name or 'Prince_George' in radar_name or 'pgr' in radar_name or \
            'PGR' in radar_name:
        cable_type = 'Belden8237'  # known checked 2015 photos  - although I3 will be LMR400
        cable_length = 600.0  # ft ??
    elif 'Inuvik' in radar_name or 'inv' in radar_name or 'INV' in radar_name:
        cable_type = 'EC400'  # checked 2017 photos.
        cable_length = 600.0  # ft ??
    elif 'Rankin Inlet' in radar_name or 'Rankin_Inlet' in radar_name or 'rkn' in radar_name or \
            'RKN' in radar_name or 'Rankin-Inlet' in radar_name:
        cable_type = 'C1180'  # known checked 2018
        cable_length = 600.0  # ft TODO verify cable length
    elif 'Clyde River' in radar_name or 'Clyde_River' in radar_name or 'cly' in radar_name or \
            'CLY' in radar_name or 'Clyde-River' in radar_name:
        cable_type = 'LMR400'  # known
        cable_length = 600.0  # ft TODO verify cable length
    else:
        sys.exit('Not a valid radar name.')

    dtypes_dict = {'freq': 'Freq*', 'vswr': 'VSWR*', 'phase_deg': 'Phase*'}
    all_data_phase_wrapped = {}
    raw_data, colour_dictionary, missing_data, data_description = \
        retrieve.retrieve_data_from_csv(plot_location + vswr_files_str, data_location,
                                        dtypes_dict)

    # Check and correct frequency array if required so all datasets are the same length
    #  with same frequency values.
    do.reduce_frequency_array(raw_data)

    # Get cable loss - this contains a loss value for all frequencies in the
    # reference_frequency list, which should directly correspond to all datasets in the
    # recorded datasets dictionary (raw_data).
    one_array_key = random.choice(list(raw_data.keys()))
    reference_frequency = list(raw_data[one_array_key]['freq'])
    cable_loss_dataset = retrieve.get_cable_loss_array(
        reference_frequency, cable_length, cable_type)

    for antenna, dataset in raw_data.items():
        # get estimated magnitude (dB loss) of single direction signal incident on the
        # balun when it reaches the end of the feedline.
        dataset_with_transmission_data = do.vswr_to_single_receive_direction(
            dataset, cable_loss_dataset)
        # Wrapping the new data with new phase for single direction.
        phase_wrapped_data = do.wrap_phase(dataset_with_transmission_data)
        all_data_phase_wrapped[antenna] = phase_wrapped_data

    for ant, dataset in raw_data.items():
        raw_data[ant] = do.wrap_phase(dataset)  # Wrap for plotting

    all_data = {}
    # Also store data that is not phase wrapped for other calculations.
    for ant, dataset in all_data_phase_wrapped.items():
        all_data[ant] = do.unwrap_phase(dataset)

    ##########################################################################
    # Getting the line of best fit for each antenna and the combined arrays,
    # and the offset from the line of best fit for each antenna and array.
    linear_fit_dict = {}
    for ant, dataset in all_data.items():
        linear_fit_dict[ant] = do.create_linear_fit_dictionary(dataset)

    # Get all main and interferometer keys
    main_data = {}
    intf_data = {}
    for ant in all_data.keys():
        if ant[0] == 'M':  # main
            main_data[ant] = all_data[ant]
        elif ant[0] == 'I':  # interferometer
            intf_data[ant] = all_data[ant]

    # Combine_arrays returns unwrapped dataset.
    unwrapped_main_array = do.combine_arrays(main_data)
    unwrapped_intf_array = do.combine_arrays(intf_data)

    # Wrapping after unwrapping ensures the first values in array are within
    # -pi to pi.
    combined_main_array = do.wrap_phase(unwrapped_main_array)
    combined_intf_array = do.wrap_phase(unwrapped_intf_array)

    linear_fit_dict['M_all'] = do.create_linear_fit_dictionary(
        unwrapped_main_array)
    linear_fit_dict['I_all'] = do.create_linear_fit_dictionary(
        unwrapped_intf_array)

    ##########################################################################
    # Computing the phase difference between the arrays and
    # also getting tdiff across the frequency range.
    array_diff_raw = []
    for m, i in zip(unwrapped_main_array, unwrapped_intf_array):
        freq = i['freq']
        phase_diff = (m['phase_deg'] - i['phase_deg'])
        array_diff_raw.append((freq, phase_diff, 0.0))
    array_diff_raw = np.array(
        array_diff_raw, dtype=[
            ('freq', 'i4'), ('phase_deg', 'f4'), ('time_ns', 'f4')])

    array_diff = do.wrap_phase(array_diff_raw)

    # Now insert the tdiff in ns after the phase has been wrapped.
    # This is the time difference between the signal incident on the main array
    # antennas reaching the end of the feedlines and the interferometer array signal
    # reaching the end of the feedlines. This is a portion of the entire path from
    # antennas to receiver. The entire path's time difference is a calibrated value
    # used in SuperDARN data analysis, and is assumed to be constant across the
    # frequency spectrum, as would be expected if the path was completely linear (such
    # as a cable).
    for dp in array_diff:
        freq = dp['freq']
        phase = dp['phase_deg']
        time_ns = phase * 1e9 / (freq * 360.0)
        dp['time_ns'] = time_ns

    ##########################################################################
    # Writing the array difference and combined arrays to file
    if time_file_str != 'None':
        array_diff.tofile(plot_location + path_type + time_file_str, sep="\n")
    if time_file_loc != 'None':
        for ant, array in all_data.items():
            array.tofile(plot_location + time_file_loc + path_type + ant + '.txt', sep="\n")
        unwrapped_main_array.tofile(plot_location + time_file_loc + path_type + 'main_array_combined.txt', sep="\n")
        unwrapped_intf_array.tofile(plot_location + time_file_loc + path_type + 'intf_array_combined.txt', sep="\n")

    ##########################################################################
    # PLOTTING
    numplots = 6
    plot_num = 0
    fig, smpplot = plt.subplots(
        numplots, 1, sharex='all', figsize=(
            18, 24), gridspec_kw={
            'height_ratios': [
                2, 2, 2, 1, 1, 1]})
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[numplots - 1].set_xlabel('Frequency (Hz)', size=25.0)
    print("plotting")
    smpplot[plot_num].set_title(plot_title, size=48.0)

    # PLOT: Phase wrapped of all data
    for ant, dataset in raw_data.items():
        smpplot[plot_num].plot(
            dataset['freq'],
            dataset['phase_deg'],
            label=ant,
            color=colour_dictionary[ant])
    smpplot[plot_num].set_ylabel('VSWR Phase All Antennas', size=25.0)
    plot_num += 1

    # PLOT: combined arrays dB and phase.
    smpplot[plot_num].plot(
        combined_main_array['freq'],
        combined_main_array['phase_deg'],
        color='#2942a8',
        label='Main Array')

    smpplot[plot_num].plot(
        combined_intf_array['freq'],
        combined_intf_array['phase_deg'],
        color='#8ba1fa',
        label='Intf Array')

    db_smpplot = smpplot[plot_num].twinx()

    db_smpplot.plot(
        combined_main_array['freq'],
        combined_main_array['magnitude'],
        color='#bd3f3f',
        label='Main Array')
    db_smpplot.plot(
        combined_intf_array['freq'],
        combined_intf_array['magnitude'],
        color='#f99191',
        label='Intf Array')

    smpplot[plot_num].set_ylabel(
        'Incoming Feedline Array\nPhase [degrees]',
        color='#3352cd',
        size=25.0)
    # blue
    smpplot[plot_num].tick_params(axis='y', labelcolor='#3352cd')

    # from antenna to feedline end at building.
    db_smpplot.set_ylabel(
        'Combined\nArray [dB]',
        color='#de4b4b',
        size=25.0)  # red
    db_smpplot.tick_params(axis='y', labelcolor='#de4b4b')
    # referenced to power at a single antenna
    plot_num += 1

    # PLOT: Time difference between arrays single direction TODO this is not 1
    # direction
    smpplot[plot_num].set_ylabel(
        'S12 Perceived Time\nDifference b/w arrays\n Based on Phase [' 'ns]', size=25.0)
    smpplot[plot_num].plot(array_diff['freq'], array_diff['time_ns'])
    plot_num += 1

    # PLOT: Main Array Offset from their Best Fit Lines, and Intf Array
    for ant, dataset in all_data.items():
        if ant[0] == 'M':  # plot with main array
            smpplot[plot_num].plot(dataset['freq'],
                                   linear_fit_dict[ant]['offset_of_best_fit_rads'] * 180.0 / math.pi,
                                   label='{}, delay={} ns'.format(ant, linear_fit_dict[ant]['time_delay_ns']),
                                   color=colour_dictionary[ant])
        elif ant[0] == 'I':
            smpplot[plot_num + 1].plot(dataset['freq'],
                                       linear_fit_dict[ant]['offset_of_best_fit_rads'] * 180.0 / math.pi,
                                       label='{}, delay={} ns'.format(ant, linear_fit_dict[ant]['time_delay_ns']),
                                       color=colour_dictionary[ant])

    smpplot[plot_num].plot(
        all_data['M0']['freq'],
        linear_fit_dict['M_all']['offset_of_best_fit_rads'] * 180.0 / math.pi,
        color=colour_dictionary['other'],
        label='Combined Main, delay={} ns'.format(
            linear_fit_dict['M_all']['time_delay_ns']))  # plot last
    smpplot[plot_num + 1].plot(all_data['M0']['freq'], linear_fit_dict['I_all'][
        'offset_of_best_fit_rads'] * 180.0 / math.pi, color=colour_dictionary['other'],
        label='Combined Intf, delay={} ns'.format(linear_fit_dict[
            'I_all']['time_delay_ns']))  # plot last

    smpplot[plot_num].legend(fontsize=10, ncol=4, loc='upper right')
    smpplot[plot_num + 1].legend(fontsize=12, loc='upper right')
    smpplot[plot_num].set_ylabel(
        'S12 Main Phase Offset\n from Own Line of Best\nFit ['
        'degrees]', size=15.0)
    smpplot[plot_num + 1].set_ylabel(
        'S12 Intf Phase Offset\n from Own Line of Best\nFit [degrees]', size=15.0)
    plot_num += 2

    # PLOT: Phase wrapped of all data
    for ant, dataset in all_data_phase_wrapped.items():
        smpplot[plot_num].plot(
            dataset['freq'],
            dataset['phase_deg'],
            label=ant,
            color=colour_dictionary[ant])
    smpplot[plot_num].set_ylabel('S12 Phase All Antennas')

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
