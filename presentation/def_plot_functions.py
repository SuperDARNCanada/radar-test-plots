import matplotlib.pyplot as plt
import math

def plot_data(working_dataframe, channels, plot_title, colour_dictionary,
                       linear_fit_dict, missing_data, data_description):
    """

    :param working_dataframe:
    :param channels:
    :param plot_title:
    :param colour_dictionary:
    :param linear_fit_dict:
    :param missing_data:
    :param data_description:
    :return:
    """

    # PLOTTING
    numplots = 5
    plot_num = 0
    fig, smpplot = plt.subplots(numplots, 1, sharex='all', figsize=(12, 12),
                                gridspec_kw={'height_ratios': [1, 2, 2, 1, 1]})
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[numplots - 1].set_xlabel('Frequency (Hz)', size=20.0)
    print("plotting")
    smpplot[plot_num].set_title(plot_title, size=24.0)

    # PLOT: Phase wrapped of all data
    for channel in channels:
        smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'],
                               working_dataframe.loc[:, channel + 'phase_deg'], label=channel,
                               color=colour_dictionary[channel])
    smpplot[plot_num].set_ylabel('Phase\nAll Channels', size=10.0)
    plot_num += 1

    combined_main_prefix = None
    combined_intf_prefix = None
    array_diff_column = None
    if 'M_all_phase_deg_unwrap' in working_dataframe.columns:
        combined_main_prefix = 'M_all_'
    elif 'M_combinedphase_deg_unwrap' in working_dataframe.columns:
        combined_main_prefix = 'M_combined'

    if 'I_all_phase_deg_unwrap' in working_dataframe.columns:
        combined_intf_prefix = 'I_all_'
    elif 'I_combinedphase_deg_unwrap' in working_dataframe.columns:
        combined_intf_prefix = 'I_combined'

    if 'M_all_phase_deg_unwrap' in working_dataframe.columns and 'I_all_phase_deg_unwrap' in \
            working_dataframe.columns:
        array_diff_column = 'array_diff_time_ns'
    elif 'M_combinedphase_deg_unwrap' and 'I_combinedphase_deg_unwrap' in working_dataframe.columns:
        array_diff_column = 'tested_array_diff_time_ns'

    # PLOT: Main Array Offset from their Best Fit Lines, and Intf Array
    for channel in channels:
        if channel[0] == 'M':  # plot with main array
            smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'], linear_fit_dict[channel][
                'offset_of_best_fit_rads'] * 180.0 / math.pi,
                                   label='{}, delay={} ns'.format(channel,
                                                                  round(linear_fit_dict[channel][
                                                                            'time_delay_ns'], 1)),
                                   color=colour_dictionary[channel])
        elif channel[0] == 'I':
            smpplot[plot_num + 1].plot(working_dataframe.loc[:, 'freq'], linear_fit_dict[channel][
                'offset_of_best_fit_rads'] * 180.0 / math.pi,
                                       label='{}, delay={} ns'.format(channel,
                                                                      round(
                                                                          linear_fit_dict[channel][
                                                                              'time_delay_ns'], 1)),
                                       color=colour_dictionary[channel])

    if combined_main_prefix:
        smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'], linear_fit_dict[combined_main_prefix][
            'offset_of_best_fit_rads'] * 180.0 / math.pi, color=colour_dictionary['other'],
                               label='Combined Main, delay={} ns'.format(round(linear_fit_dict[
                                                                                   combined_main_prefix][
                                                                                   'time_delay_ns'],
                                                                               1)))  # plot last
    if combined_intf_prefix:
        smpplot[plot_num + 1].plot(working_dataframe.loc[:, 'freq'], linear_fit_dict[combined_intf_prefix][
            'offset_of_best_fit_rads'] * 180.0 / math.pi, color=colour_dictionary['other'],
                                   label='Combined Intf, delay={} ns'.format(round(linear_fit_dict[
                                                                                       combined_intf_prefix][
                                                                                       'time_delay_ns'],
                                                                                   1)))  # plot last

    # smpplot[plot_num].legend(fontsize=7, ncol=4, loc='upper right')
    # handles, labels = smpplot[plot_num].get_legend_handles_labels()
    box = smpplot[plot_num].get_position()
    smpplot[plot_num].set_position([box.x0, box.y0 + box.height * 0.37,
                                    box.width, box.height * 0.63])
    smpplot[plot_num].legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                             fancybox=True, shadow=True, ncol=5, fontsize=9)
    box = smpplot[plot_num + 1].get_position()
    smpplot[plot_num + 1].set_position([box.x0, box.y0 + box.height * 0.15,
                                        box.width, box.height * 0.85])
    smpplot[plot_num + 1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                                 fancybox=True, shadow=True, ncol=5, fontsize=9)
    # smpplot[plot_num].legend(fontsize=8, ncol=4, loc='lower center')
    # smpplot[plot_num + 1].legend(fontsize=12, loc='upper right')

    smpplot[plot_num].set_ylabel('Main Array Offsets\nfrom Fit ['
                                 'degrees]', size=10.0)
    smpplot[plot_num + 1].set_ylabel('Intf Array Offsets\n from Fit [degrees]', size=10.0)
    plot_num += 2


    if combined_main_prefix:
        # PLOT: combined arrays dB and phase.
        smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'],
                               working_dataframe.loc[:, combined_main_prefix + 'phase_deg'],
                               color='#2942a8', label='Main Array')

    if combined_intf_prefix:
        smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'],
                               working_dataframe.loc[:, combined_intf_prefix + 'phase_deg'],
                               color='#8ba1fa', label='Intf Array')

    db_smpplot = smpplot[plot_num].twinx()

    if combined_main_prefix:
        db_smpplot.plot(working_dataframe.loc[:, 'freq'], working_dataframe.loc[:, combined_main_prefix + 'magnitude'],
                        color='#bd3f3f', label='Main Array')

    if combined_intf_prefix:
        db_smpplot.plot(working_dataframe.loc[:, 'freq'], working_dataframe.loc[:,
                                                          combined_intf_prefix + 'magnitude'],
                        color='#f99191', label='Intf Array')

    smpplot[plot_num].set_ylabel('Array Phase\n[degrees]', color='#3352cd',
                                     size=10.0)
    # blue
    smpplot[plot_num].tick_params(axis='y', labelcolor='#3352cd')

    # from antenna to feedline end at building.
    db_smpplot.set_ylabel('Combined\nArray [dB]', color='#de4b4b', size=10.0)  # red
    db_smpplot.tick_params(axis='y', labelcolor='#de4b4b')
    # referenced to power at a single antenna
    plot_num += 1

    if array_diff_column:
        # PLOT: Time difference between arrays single direction TODO this is not 1 direction

        smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'],
                               working_dataframe.loc[:, array_diff_column], )
    smpplot[plot_num].set_ylabel('Time Delay\nBetween Arrays [ns]', size=10.0)
    plot_num += 1

    if missing_data:  # not empty
        missing_data_statement = "***MISSING DATA FROM CHANNEL(S) "
        for element in missing_data:
            missing_data_statement = missing_data_statement + element + " "
        print(missing_data_statement)
        #plt.figtext(0.3, 0.02, missing_data_statement, fontsize=7)

    if data_description:
        print(data_description)
        #plt.figtext(0.3, 0.05, data_description, fontsize=7)

    for plot in range(0, numplots):
        smpplot[plot].grid()


def plot_transmitter_path(working_dataframe, channels, plot_title, colour_dictionary,
                       linear_fit_dict, missing_data, data_description):
    """

    :param working_dataframe:
    :param channels:
    :param plot_title:
    :param colour_dictionary:
    :param linear_fit_dict:
    :param missing_data:
    :param data_description:
    :return:
    """
    # PLOTTING
    numplots = 6
    plot_num = 0
    fig, smpplot = plt.subplots(numplots, 1, sharex='all', figsize=(12, 12),
                                gridspec_kw={'height_ratios': [1, 1, 1, 2, 1.5, 1]})
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[numplots - 1].set_xlabel('Frequency (Hz)', size=20.0)
    print("plotting")
    smpplot[plot_num].set_title(plot_title, size=24.0)

    # PLOT: Phase wrapped of all data
    for channel in channels:
        smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'],
                               working_dataframe.loc[:, channel + 'phase_deg'], label=channel,
                               color=colour_dictionary[channel])
    smpplot[plot_num].set_ylabel('Phase All\nChannels [degrees]', size=10.0)
    plot_num += 1

    # PLOT: combined arrays dB and phase.
    smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'],
                           working_dataframe.loc[:, 'M_all_phase_deg'],
                           color='#2942a8', label='Main Array')

    smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'],
                           working_dataframe.loc[:, 'I_all_phase_deg'],
                           color='#8ba1fa', label='Intf Array')

    db_smpplot = smpplot[plot_num].twinx()

    db_smpplot.plot(working_dataframe.loc[:, 'freq'], working_dataframe.loc[:, 'M_all_magnitude'],
                    color='#bd3f3f', label='Main Array')
    db_smpplot.plot(working_dataframe.loc[:, 'freq'], working_dataframe.loc[:, 'I_all_magnitude'],
                    color='#f99191', label='Intf Array')

    smpplot[plot_num].set_ylabel('Array Phase\n[degrees]', color='#3352cd',
                                 size=10.0)
    # blue
    smpplot[plot_num].tick_params(axis='y', labelcolor='#3352cd')

    # from antenna to feedline end at building.
    db_smpplot.set_ylabel('Combined\nArray [dB]', color='#de4b4b', size=10.0)  # red
    db_smpplot.tick_params(axis='y', labelcolor='#de4b4b')
    # referenced to power at a single antenna
    plot_num += 1

    # PLOT: Time difference between arrays single direction TODO this is not 1 direction
    smpplot[plot_num].set_ylabel('Time Delay\nBetween Arrays [ns]', size=10.0)
    smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'],
                           working_dataframe.loc[:, 'array_diff_time_ns'], )
    plot_num += 1

    # PLOT: Main Array Offset from their Best Fit Lines, and Intf Array
    for channel in channels:
        if channel[0] == 'M':  # plot with main array
            smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'], linear_fit_dict[channel][
                'offset_of_best_fit_rads'] * 180.0 / math.pi,
                                   label='{}, delay={} ns'.format(channel,
                                                                  round(linear_fit_dict[channel][
                                                                            'time_delay_ns'], 1)),
                                   color=colour_dictionary[channel])
        elif channel[0] == 'I':
            smpplot[plot_num + 1].plot(working_dataframe.loc[:, 'freq'], linear_fit_dict[channel][
                'offset_of_best_fit_rads'] * 180.0 / math.pi,
                                       label='{}, delay={} ns'.format(channel,
                                                                      round(
                                                                          linear_fit_dict[channel][
                                                                              'time_delay_ns'], 1)),
                                       color=colour_dictionary[channel])

    smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'], linear_fit_dict['M_all_'][
        'offset_of_best_fit_rads'] * 180.0 / math.pi, color=colour_dictionary['other'],
                           label='Combined Main, delay={} ns'.format(round(linear_fit_dict[
                                                                               'M_all_'][
                                                                               'time_delay_ns'],
                                                                           1)))  # plot last
    smpplot[plot_num + 1].plot(working_dataframe.loc[:, 'freq'], linear_fit_dict['I_all_'][
        'offset_of_best_fit_rads'] * 180.0 / math.pi, color=colour_dictionary['other'],
                               label='Combined Intf, delay={} ns'.format(round(linear_fit_dict[
                                                                                   'I_all_'][
                                                                                   'time_delay_ns'],
                                                                               1)))  # plot last

    # smpplot[plot_num].legend(fontsize=7, ncol=4, loc='upper right')
    # handles, labels = smpplot[plot_num].get_legend_handles_labels()
    box = smpplot[plot_num].get_position()
    smpplot[plot_num].set_position([box.x0, box.y0 + box.height * 0.37,
                                    box.width, box.height * 0.63])
    smpplot[plot_num].legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                             fancybox=True, shadow=True, ncol=5, fontsize=9)
    box = smpplot[plot_num + 1].get_position()
    smpplot[plot_num + 1].set_position([box.x0, box.y0 + box.height * 0.15,
                                        box.width, box.height * 0.85])
    smpplot[plot_num + 1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                                 fancybox=True, shadow=True, ncol=5, fontsize=9)
    # smpplot[plot_num].legend(fontsize=8, ncol=4, loc='lower center')
    # smpplot[plot_num + 1].legend(fontsize=12, loc='upper right')

    smpplot[plot_num].set_ylabel('Main Array Offsets\nfrom Fit ['
                                 'degrees]', size=10.0)
    smpplot[plot_num + 1].set_ylabel('Intf Array Offsets\n from Fit [degrees]', size=10.0)
    plot_num += 2

    # PLOT: Phase wrapped of all data
    for channel in channels:
        smpplot[plot_num].plot(working_dataframe.loc[:, 'freq'],
                               working_dataframe.loc[:, channel + 'phase_deg'], label=channel,
                               color=colour_dictionary[channel])
    smpplot[plot_num].set_ylabel('S12 Phase All Antennas', fontsize=10.0)

    # fig.legend(handles, labels, loc=7)

    if missing_data:  # not empty
        missing_data_statement = "***MISSING DATA FROM CHANNEL(S) "
        for element in missing_data:
            missing_data_statement = missing_data_statement + element + " "
        print(missing_data_statement)
        plt.figtext(0.3, 0.02, missing_data_statement, fontsize=7)

    if data_description:
        print(data_description)
        plt.figtext(0.3, 0.05, data_description, fontsize=7)

    for plot in range(0, numplots):
        smpplot[plot].grid()
