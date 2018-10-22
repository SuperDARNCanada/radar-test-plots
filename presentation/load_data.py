import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import fnmatch
import pandas as pd
pd.options.mode.chained_assignment = None
import json
import sys
import random
sys.path.append('../tdiff_path/')

# import some modules that I created to do some data processing.

import dataset_operations.dataset_operations as do
import retrieve_data.retrieve_data as retrieve

# I have metadata for all the datasets I have available stored in a csv.
site_file_metadata=pd.read_csv('site_file_metadata.csv')

hex_colors = ['#ff1a1a', '#993300', '#ffff1a', '#666600', '#ff531a', '#cc9900', '#99cc00',
              '#7a7a52', '#004d00', '#33ff33', '#26734d', '#003366', '#33cccc', '#00004d',
              '#5500ff', '#a366ff', '#ff00ff', '#e6005c', '#ffaa80', '#999999', '#994455',
              '#44ee23']
colour_dictionary = {'other': '#000000'}

# subsetting for data from specific site, date, and data type.

#working_site = 'PGR'
#working_date = 20170930
#working_data_type = 'feedline-VSWR'
working_metadata_index = int(sys.argv[1])


# data_type_metadata = site_file_metadata[site_file_metadata['data_type']==working_data_type]
# site_to_data = {}
#
# for site in data_type_metadata.site.unique():
#     site_to_data[site] = data_type_metadata[data_type_metadata['site']==site]
#
# # choose a site and a date for the metadata we want to use.
#
# working_metadata = site_to_data[working_site].loc[site_to_data[working_site]['date'] ==
#                                                   working_date, :]

filename = str(site_file_metadata.iloc[working_metadata_index]['mapping_filename'])
data_loc = str(site_file_metadata.iloc[working_metadata_index]['data_location'])
working_site = str(site_file_metadata.iloc[working_metadata_index]['site'])
working_date = int(site_file_metadata.iloc[working_metadata_index]['date'])
working_data_type = str(site_file_metadata.iloc[working_metadata_index]['data_type'])
interim_data_bool = bool(site_file_metadata.iloc[working_metadata_index]['interim_data'])
print(site_file_metadata.iloc[working_metadata_index])
plot_title = working_site + ' ' + str(working_date) + ' ' + working_data_type

with open(filename, 'r') as f:
    mapping_dict = json.load(f)
working_channel_data = {}

if working_data_type == 'feedline-VSWR':
    # data we care about from the VSWR channel - there are multiple sweeps in the files and some empty columns.
    good_columns = {'Freq. [Hz]': 'freq', 'VSWR [(VSWR)]': 'vswr', 'Phase []': 'phase_deg'}
elif working_data_type == 'transmitter-path' or working_data_type == 'pm-path':
    good_columns = {'Freq. [Hz]': 'freq', 'Magnitude [dB]': 'magnitude', 'Phase []': 'phase_deg'}
else:
    print('Working data type {} is not recognized.'.format(working_data_type))

data_description = ''
missing_data = []
attenuator_flag = False
for channel_name, channel_file in mapping_dict.items():
    if channel_name == '_comment':
        data_description = channel_file
        continue
    if channel_file == 'dne':
        missing_data.append(channel_name)
        continue
    if channel_name == 'atten':  # used for phasing matrix value of attenuators
        attenuator_flag = True
        attenuation = float(channel_file)
        continue
    if channel_name == 'atten_file':  # used for phasing matrix transmission through attenuators
        attenuator_flag = True
        continue
    if channel_file == 'estimate_intf':
        print('\nEstimation required for interferometer channel {}'.format(channel_name))
        continue  # TODO create an estimate for this data.
    #print(channel_file)
    # find the header.
    with open(data_loc + channel_file, 'r') as csvfile:
        for line_num, line in enumerate(csvfile):
            if fnmatch.fnmatch(line, 'Freq. [Hz*'):  # skip to header
                header_line = line_num - 1
                #print(line)
                #print('header is {}'.format(header_line))
                break
    working_channel_data[channel_name] = pd.read_csv(data_loc + channel_file, header=header_line)
    #print(working_channel_data[channel_name].head())
    working_channel_data[channel_name] = working_channel_data[channel_name].loc[:,
        list(good_columns.keys())]
    rename_dict = {}
    for k, v in good_columns.items():
        if k != 'Freq. [Hz]':
            rename_dict[k] = channel_name + v
        else:
            rename_dict[k] = v
    working_channel_data[channel_name] = working_channel_data[channel_name].rename(
        rename_dict, axis='columns')

if missing_data:
    print('\nThere is missing data from the following channel(s): {}'.format(missing_data))
if data_description != '':
    print('\nThere is a data description associated with this data:')
    print(data_description)

# ensure all dataframes have the same frequency array.
working_channel_data = do.reduce_frequency_array(working_channel_data)

# create a single dataframe with all data.
reference_frequency = working_channel_data[random.choice(list(working_channel_data.keys()))]['freq'].astype(int)
# remove the reference frequency array from all dataframes
new_data = {}
for ant, data in working_channel_data.items():
    new_data[ant] = data.drop(columns=['freq'])

all_dataframes = [df for key, df in new_data.items()]
joined_list = [reference_frequency] + all_dataframes
working_dataframe = pd.concat(joined_list, axis=1)
del new_data
channels = working_channel_data.keys()

if working_data_type == 'feedline-VSWR':
    # Feedline metadata is necessary to get a cable loss model.
    feedline_metadata = pd.read_csv('site_feedline_metadata.csv')
    cable_loss_dataset_dict = {}
    working_feedline_metadata = feedline_metadata[feedline_metadata['site'] == working_site]
    for index, row in working_feedline_metadata.iterrows():
        dict_key = row['array'] + str(row['feedline_number'])
        cable_loss_dataset_dict[dict_key] = retrieve.get_cable_loss_array(reference_frequency, row['cable_length_ft'], row['cable_type'])

if working_data_type == 'pm-path':
    if attenuator_flag:
        if 'atten_file' in channels:
            channels.pop('atten_file')
            for channel in channels:
                working_channel_data[channel].loc[:, channel + 'phase_deg'] = np.array(
                    working_channel_data[channel].loc[:, channel + 'phase_deg']) - np.array(
                    working_channel_data['atten_file'].loc[:, 'atten_filephase_deg'])
                working_channel_data[channel].loc[:, channel + 'magnitude'] = np.array(
                    working_channel_data[channel].loc[:, channel + 'magnitude']) - np.array(
                    working_channel_data['atten_file'].loc[:, 'atten_filemagnitude'])
            del working_channel_data['atten_file']
        else:  # float attenuation
            for channel in channels:
                working_channel_data[channel].loc[:, channel + 'magnitude'] = np.array(
                    working_channel_data[channel].loc[:, channel + 'magnitude']) - attenuation
                # phase will not change, but phase difference between channels should still
                # be accurate because all channels had the same attenuation.

for channel in channels:
    # get estimated magnitude (dB loss) of single direction signal incident on the
    # balun when it reaches the end of the feedline.
    # get slice of the dataframe dealing with this data.
    colour_dictionary[channel] = hex_colors.pop(0)
    if working_data_type == 'feedline-VSWR':
        dataset = working_dataframe.loc[:,
                  ['freq', channel + 'vswr', channel + 'phase_deg']].rename(
            {channel + 'vswr': 'vswr', channel + 'phase_deg': 'phase_deg'}, axis='columns')
        dataset_with_transmission_data = do.vswr_to_single_receive_direction(
            channel, dataset, cable_loss_dataset_dict[channel])
        # Wrapping the new data with new phase for single direction.
        phase_wrapped_data = do.wrap_phase(dataset_with_transmission_data)
        working_dataframe.loc[:, channel + 'vswr'] = phase_wrapped_data['vswr']
    else:
        dataset = working_dataframe.loc[:,
                  ['freq', channel + 'magnitude', channel + 'phase_deg']].rename(
            {channel + 'magnitude': 'magnitude', channel + 'phase_deg': 'phase_deg'},
            axis='columns')
        phase_wrapped_data = do.wrap_phase(dataset)

    working_dataframe.loc[:, channel + 'phase_deg'] = phase_wrapped_data['phase_deg']
    working_dataframe.loc[:, channel + 'magnitude'] = phase_wrapped_data['magnitude']
    unwrapped_phase_data = do.unwrap_phase(phase_wrapped_data)
    working_dataframe.loc[:, channel + 'phase_deg_unwrap'] = unwrapped_phase_data['phase_deg']

# Also store data that is not phase wrapped for other calculations.

# Getting the line of best fit for each antenna and the combined arrays,
# and the offset from the line of best fit for each antenna and array.

linear_fit_dict = {}
for channel in channels:
    dataset = working_dataframe.loc[:,['freq', channel+'phase_deg_unwrap']].rename({channel+'phase_deg_unwrap': 'phase_deg'}, axis='columns')
    # create phase_rad column.
    dataset.loc[:,'phase_rad'] = np.array(dataset.loc[:,['phase_deg']]) * math.pi / 180.0
    working_dataframe.loc[:,channel+'phase_rad'] = dataset.loc[:,'phase_rad']
    linear_fit_dict[channel] = do.create_linear_fit_dictionary(dataset)

# combining arrays
main_channels = []
intf_channels = []
for channel in channels:
    if channel[0] == 'M' and 'combined' not in channel:  # main
        main_channels.append(channel)
    elif channel[0] == 'I' and 'combined' not in channel:  # interferometer
        intf_channels.append(channel)

if main_channels:  # not empty
    # Combine_arrays returns unwrapped dataset.
    main_data = []

    for channel in main_channels:
        main_data.append(working_dataframe.loc[:,['freq', channel+'phase_rad', channel+'magnitude']].rename({channel+'phase_rad': 'phase_rad', channel+'magnitude':'magnitude'}, axis='columns'))
    unwrapped_main_data = do.combine_arrays(main_data)


    working_dataframe.loc[:,'M_all_phase_deg_unwrap'] = np.array(unwrapped_main_data.loc[:,['phase_rad']]) * 180.0 / math.pi
    working_dataframe.loc[:,'M_all_phase_rad'] = unwrapped_main_data.loc[:,'phase_rad']


    # Wrapping after unwrapping ensures the first values in array are within -pi to pi.
    combined_main_array = do.wrap_phase(unwrapped_main_data)

    working_dataframe.loc[:,'M_all_phase_deg'] = np.array(combined_main_array.loc[:,['phase_rad']]) * 180.0 / math.pi
    working_dataframe.loc[:,'M_all_magnitude'] = combined_main_array.loc[:,'magnitude']

    linear_fit_dict['M_all_'] = do.create_linear_fit_dictionary(unwrapped_main_data)
else:
    print('\nNo combined main array data was calculated because there is no individual channel '
          'data.')
if intf_channels:  # not empty
    intf_data = []
    for channel in intf_channels:
        intf_data.append(working_dataframe.loc[:,['freq', channel+'phase_rad', channel+'magnitude']].rename({channel+'phase_rad': 'phase_rad', channel+'magnitude':'magnitude'}, axis='columns'))
    unwrapped_intf_data = do.combine_arrays(intf_data)
    working_dataframe.loc[:,'I_all_phase_deg_unwrap'] = np.array(unwrapped_intf_data.loc[:,['phase_rad']]) * 180.0 / math.pi
    working_dataframe.loc[:,'I_all_phase_rad'] = unwrapped_intf_data.loc[:,'phase_rad']
    combined_intf_array = do.wrap_phase(unwrapped_intf_data)
    working_dataframe.loc[:, 'I_all_phase_deg'] = np.array(
        combined_intf_array.loc[:, ['phase_rad']]) * 180.0 / math.pi
    working_dataframe.loc[:, 'I_all_magnitude'] = combined_intf_array.loc[:, 'magnitude']
    linear_fit_dict['I_all_'] = do.create_linear_fit_dictionary(unwrapped_intf_data)
else:
    print('\nNo combined interferometer array data was calculated because there is no individual '
          'channel data.')


##################################################################
# Get the array differences.


if 'M_all_phase_deg_unwrap' and 'I_all_phase_deg_unwrap' in working_dataframe.columns:
    # calculate array difference
    # Computing the phase difference between the arrays and
    # also getting tdiff across the frequency range.
    array_diff = []
    for m, i in zip(working_dataframe.loc[:, 'M_all_phase_deg_unwrap'],
                    working_dataframe.loc[:, 'I_all_phase_deg_unwrap']):
        phase_diff = m - i
        array_diff.append(phase_diff)
    array_diff = do.wrap_phase(pd.DataFrame(np.array(array_diff), columns=['phase_deg']))
    if 'array_diff_phase_deg' not in working_dataframe.columns:
        working_dataframe = pd.concat([working_dataframe,
                                       array_diff.rename({'phase_deg': 'array_diff_phase_deg'},
                                                         axis='columns')], axis='columns')
    else:
        working_dataframe['array_diff_phase_deg'] = array_diff

    # Now insert the tdiff in ns after the phase has been wrapped.
    # This is the time difference between the signal incident on the main array
    # antennas reaching the end of the feedlines and the interferometer array signal
    # reaching the end of the feedlines. This is a portion of the entire path from
    # antennas to receiver. The entire path's time difference is a calibrated value
    # used in SuperDARN data analysis, and is assumed to be constant across the
    # frequency spectrum, as would be expected if the path was completely linear (such
    # as a cable).
    time_ns_list = []
    for num, dp in array_diff.iterrows():
        freq = working_dataframe['freq'][num]
        phase = dp
        time_ns = phase * 1e9 / (freq * 360.0)
        time_ns_list.append(time_ns)
    if 'array_diff_time_ns' not in working_dataframe.columns:
        working_dataframe = pd.concat([working_dataframe, pd.DataFrame(np.array(time_ns_list),
                                                                       columns=[
                                                                           'array_diff_time_ns'])],
                                      axis='columns')
    else:
        working_dataframe['array_diff_time_ns'] = pd.DataFrame(np.array(time_ns_list),
                                                               columns=['array_diff_time_ns'])

if 'M_combinedphase_deg_unwrap' and 'I_combinedphase_deg_unwrap' in working_dataframe.columns:
    # calculate array difference
    # Computing the phase difference between the arrays and
    # also getting tdiff across the frequency range.
    array_diff = []
    for m, i in zip(working_dataframe.loc[:, 'M_combinedphase_deg_unwrap'],
                    working_dataframe.loc[:, 'I_combinedphase_deg_unwrap']):
        phase_diff = m - i
        array_diff.append(phase_diff)
    array_diff = do.wrap_phase(pd.DataFrame(np.array(array_diff), columns=['phase_deg']))
    if 'array_diff_phase_deg' not in working_dataframe.columns:
        working_dataframe = pd.concat([working_dataframe, array_diff.rename(
            {'phase_deg': 'tested_array_diff_phase_deg'}, axis='columns')], axis='columns')
    else:
        working_dataframe['tested_array_diff_phase_deg'] = array_diff

    # Now insert the tdiff in ns after the phase has been wrapped.
    # This is the time difference between the signal incident on the main array
    # antennas reaching the end of the feedlines and the interferometer array signal
    # reaching the end of the feedlines. This is a portion of the entire path from
    # antennas to receiver. The entire path's time difference is a calibrated value
    # used in SuperDARN data analysis, and is assumed to be constant across the
    # frequency spectrum, as would be expected if the path was completely linear (such
    # as a cable).
    time_ns_list = []
    for num, dp in array_diff.iterrows():
        freq = working_dataframe['freq'][num]
        phase = dp
        time_ns = phase * 1e9 / (freq * 360.0)
        time_ns_list.append(time_ns)
    if 'array_diff_time_ns' not in working_dataframe.columns:
        working_dataframe = pd.concat([working_dataframe, pd.DataFrame(np.array(time_ns_list),
                                                                       columns=[
                                                                           'tested_array_diff_time_ns'])],
                                      axis='columns')
    else:
        working_dataframe['array_diff_time_ns'] = pd.DataFrame(np.array(time_ns_list), columns=[
            'tested_array_diff_time_ns'])

print('\nThe data has been successfully loaded.')
# print('I have calculated combined datasets for the entire array from the individual channels in '
#       'that array.\n')
#
# print('Here is a few lines from the working dataframe:\n')
# print(working_dataframe.head())

#
# print('\n')
# print('We have also created a linear fit dictionary using the phase arrays from each channel.\n')
