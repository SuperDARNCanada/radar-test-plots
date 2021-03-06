#!/usr/bin/python

# plot_vswrs.py
# To plot all VSWR data on the same plot to visualize
# differences between the antennas.

import sys
import fnmatch
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import json
import csv

sys.path.append('/home/shared/code/radar-test-plots/tdiff_path')

from dataset_operations.dataset_operations import reduce_frequency_array, wrap_phase, \
    unwrap_phase

# General variables to change depending on data being used
radar_name = sys.argv[1]  # eg. Inuvik
data_location = sys.argv[2]  # eg. '/home/shared/Sync/Sites/Inuvik/Trips/2017/Datasets/'
plot_location = sys.argv[3]  # eg. '/home/shared/Sync/Sites/Inuvik/Trips/2017/Data_Analysis/VSWRs/'
vswr_files_str = sys.argv[4]  # eg. 'vswr-files.json' - must be located in plot_location.
#vswr_intf_files_str = sys.argv[5]  # eg. 'vswr-intf-files.json' - must be location in plot_location.
plot_filename = radar_name + ' vswrs.png'

print(radar_name, data_location, plot_location, vswr_files_str, plot_filename)

# number_of_data_points = 801
vswrs_plot_title = radar_name + ' Feedline to Antenna Standing Wave Ratios'

sys.path.append(data_location)

# TODO get date from csv files
with open(plot_location + vswr_files_str) as f:
    vswr_files = json.load(f)

    all_files = vswr_files
    print("All files: {}".format(vswr_files))
#
#
# A list of 21 colors that will be assigned to antennas to keep plot colors consistent.
hex_colors = ['#ff1a1a', '#993300', '#ffff1a', '#666600', '#ff531a', '#cc9900', '#99cc00',
              '#7a7a52', '#004d00', '#33ff33', '#26734d', '#003366', '#33cccc', '#00004d',
              '#5500ff', '#a366ff', '#ff00ff', '#e6005c', '#ffaa80', '#999999']
hex_dictionary = {'other': '#000000'}


def main():
    data_description = []
    missing_data = []
    all_data = {}

    for ant, v in all_files.items():
        if ant == '_comment':
            data_description = v
            continue
        if v == 'dne':
            missing_data.append(ant)
            continue
        with open(data_location + v, 'r') as csvfile:
            for line in csvfile:
                # skip to header
                if fnmatch.fnmatch(line, 'Freq [Hz*') or fnmatch.fnmatch(line, 'Frequency [Hz*'):
                    break
            else:  # no break
                sys.exit('No data in file {}\n'.format(v))
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
                    print(freq_column, vswr_column, phase_column)
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
                    vswr = float(row[vswr_column])
                    phase = float(row[phase_column])
                    data.append((freq, vswr, phase))
                except:
                    continue
            data = np.array(data, dtype=[('freq', 'i4'), ('VSWR', 'f4'), ('phase', 'f4')])

            all_data[ant] = data
            hex_dictionary[ant] = hex_colors[0]
            hex_colors.remove(hex_dictionary[ant])

    all_data = reduce_frequency_array(all_data)

    all_data_phase_wrapped = {}
    for ant, dataset in all_data.items():
        all_data_phase_wrapped[ant] = wrap_phase(dataset)

    for ant, dataset in all_data_phase_wrapped.items():
        all_data[ant] = unwrap_phase(dataset)  # wrapping then unwrapping allows us to
        # get rid of any 360 degree offset in the measurements.


    max_phase = list(all_data['M0']['phase'])
    min_phase = list(all_data['M0']['phase'])
    phase_ave = list(all_data['M0']['phase'])
    swr_ave = list(all_data['M0']['VSWR'])
    for ant, dataset in all_data.items():
        for index, entry in enumerate(dataset):
            if entry['phase'] < min_phase[index]:
                min_phase[index] = entry['phase']
            if entry['phase'] > max_phase[index]:
                max_phase[index] = entry['phase']
        if ant == 'M0':
            pass
        else:
            swr_ave = [swr_ave[i] + dataset['VSWR'][i] for i in range(len(dataset))]
            phase_ave = [phase_ave[i] + dataset['phase'][i] for i in range(len(dataset))]
    diff_phase = [(max_phase[i] - min_phase[i]) for i in range(len(min_phase))]
    swr_ave = [swr_ave[i]/20 for i in range(len(swr_ave))]
    phase_ave = [phase_ave[i]/20 for i in range(len(phase_ave))]

    # for each antenna, get the linear fit and plot the offset from linear fit.
    linear_fit_dict = {}
    for ant, dataset in all_data.items():
        slope, intercept, rvalue, pvalue, stderr = stats.linregress(dataset['freq'],
                                                                    dataset['phase'])
        linear_fit_dict[ant] = {'slope': slope, 'intercept': intercept, 'rvalue': rvalue,
                                'pvalue': pvalue, 'stderr': stderr}
        offset_of_best_fit = []
        best_fit_line = []
        for entry in dataset:
            best_fit_value = slope * entry['freq'] + intercept
            offset_of_best_fit.append(entry['phase'] - best_fit_value)
            best_fit_line.append(best_fit_value)
        best_fit_line = np.array(best_fit_line, dtype=[('phase', 'f4')])
        offset_of_best_fit = np.array(offset_of_best_fit, dtype=[('phase', 'f4')])
        offset_of_best_fit = wrap_phase(offset_of_best_fit)
        linear_fit_dict[ant]['offset_of_best_fit'] = offset_of_best_fit['phase']
        linear_fit_dict[ant]['best_fit_line'] = best_fit_line
        linear_fit_dict[ant]['best_fit_line'] = wrap_phase(linear_fit_dict[ant][
                                                               'best_fit_line'])

    # find top antennas with highest phase offsets and plot those antennas SWR
    furthest_phase_offset = {}
    for ant, dataset in all_data.items():
        max_phase_offset = 0
        for index, entry in enumerate(dataset):
            phase_offset = abs(entry['phase'] - phase_ave[index])
            if phase_offset > max_phase_offset:
                max_phase_offset = phase_offset
        furthest_phase_offset[ant] = max_phase_offset
    worst_swrs = []
    while len(worst_swrs) < 5:
        worst_swrs.append(max(furthest_phase_offset, key=lambda key: furthest_phase_offset[key]))
        del furthest_phase_offset[worst_swrs[-1]]

    worst_swrs_phase_offset = {}
    for antenna in worst_swrs:
        phase_offset_list = all_data[antenna]['phase'] - phase_ave
        worst_swrs_phase_offset[antenna] = np.array(phase_offset_list, dtype=[('phase',
                                                                               'f4')])
        worst_swrs_phase_offset[antenna] = wrap_phase(worst_swrs_phase_offset[antenna])

    numplots = 6
    fig, smpplot = plt.subplots(numplots, sharex=True, figsize=(16, 22), dpi=80)
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[0].set_title(vswrs_plot_title, size=30, linespacing=1.3)
    for ant, dataset in all_data_phase_wrapped.items():
        smpplot[0].plot(dataset['freq'], dataset['phase'], label=ant,
                    color=hex_dictionary[ant])
    for ant, dataset in all_data.items():
        smpplot[1].plot(dataset['freq'], dataset['VSWR'], label=ant, color=hex_dictionary[ant])
        smpplot[4].plot(dataset['freq'], linear_fit_dict[ant]['offset_of_best_fit'],
                        label='{}, stderr={}'.format(ant,round(linear_fit_dict[ant]['stderr'], 9)),
                        color=hex_dictionary[ant])
    # smpplot[2].plot(all_data['M0']['freq'], diff_phase, label='Max-Min Difference',
    #                 color=hex_dictionary['other'])
    smpplot[3].plot(all_data['M0']['freq'], swr_ave, label='Average SWR',
                    color=hex_dictionary['other'])
    for antenna in worst_swrs:
        smpplot[3].plot(all_data[antenna]['freq'], all_data[antenna]['VSWR'], label=antenna,
                        color=hex_dictionary[antenna])
        smpplot[2].plot(all_data[antenna]['freq'], worst_swrs_phase_offset[antenna],
                        label=antenna, color=hex_dictionary[antenna])
    smpplot[4].set_xlabel('Frequency (Hz)', size='xx-large')
    smpplot[0].set_ylabel('Phase [degrees]', size='xx-large')
    smpplot[1].set_ylabel('VSWR', size='xx-large')
    smpplot[2].set_ylabel('Worst Phase Offsets\n from Average', size='xx-large')
    smpplot[3].set_ylabel('Worst VSWRs by Phase', size='xx-large')
    for i in range(0, numplots):
        smpplot[i].grid()
    smpplot[2].legend(fontsize=10)
    smpplot[3].legend(fontsize=10)
    smpplot[4].legend(fontsize=7, loc='upper right', ncol=3)
    smpplot[4].set_ylabel('Phase Offsets from\nLine of Best Fit', size='xx-large')
    #plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
    #           ncol=2, mode="expand", borderaxespad=0.)
    print("plotting")
    if missing_data:  # not empty
        missing_data_statement = "***MISSING DATA FROM ANTENNA(S) "
        for element in missing_data:
            missing_data_statement = missing_data_statement + element + " "
        print(missing_data_statement)
        plt.figtext(0.65, 0.05, missing_data_statement, fontsize=15)
    else:
        print("No missing data")

    if data_description:
        print("Data description: {}".format(data_description))

        plt.figtext(0.65, 0.10, data_description, fontsize=15)

    fig.savefig(plot_location + plot_filename)
    plt.close(fig)
    print("Figure saved at: {}".format(plot_location + plot_filename))


if __name__ == main():
    main()
