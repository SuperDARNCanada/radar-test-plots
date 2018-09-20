import json
import fnmatch
import sys
import csv
import math
import numpy as np

#
#
# A list of 21 colors that will be assigned to antennas to keep plot colors consistent.
hex_colors = ['#ff1a1a', '#993300', '#ffff1a', '#666600', '#ff531a', '#cc9900', '#99cc00',
              '#7a7a52', '#004d00', '#33ff33', '#26734d', '#003366', '#33cccc', '#00004d',
              '#5500ff', '#a366ff', '#ff00ff', '#e6005c', '#ffaa80', '#999999']
colour_dictionary = {'other': '#000000'}


def retrieve_data_from_csv(map_to_files, data_location, header_names):
    """
    Get the data from the csv files given in the json file provided.
    :param: map_to_files: json file location with map of antenna : file with dataset in 
    csv format.
    :param: data_location: location of the data files specified in the map_to_files file.
    :param: header_names: Dictionary with dtype key and string value to search for in 
    the csv file. e.g. { 'freq': 'Freq*', 'vswr': 'VSWR*', 'phase_deg': 'Phase*'}
    :return: all_data: dictionary of antenna to dataset
    :return: missing_data: list of any antennas with 'dne' values in map_to_files
    :return: colour_dictionary: dictionary of antenna to colour. 
    """

    with open(map_to_files) as f:
        vswr_files = json.load(f)

    # Rename this to phase_deg if named phase by mistake.
    if 'phase' in header_names:
        header_names['phase_deg'] = header_names.pop('phase')

    dtypes = []  # List of dtype names only
    array_dtypes = []  # List of tuples (name, type) for array creation.
    for dtype in header_names.keys():
        dtypes.append(dtype)
        if dtype == 'freq':
            value_type = 'i4'
        else:
            value_type = 'f4'
        array_dtypes.append((dtype, value_type))
        if dtype == 'phase_deg':
            dtypes.append('phase_rad')
            array_dtypes.append(('phase_rad', 'f4'))

    print(array_dtypes)

    data_description = []
    missing_data = []
    all_data = {}
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
            dtype_to_column = {}
            for dtype, dtype_string in header_names.items():
                try:
                    matching_columns = [i for i in range(len(row)) if
                                    fnmatch.fnmatch(row[i], dtype_string)]
                    first_column = matching_columns[0]
                    dtype_to_column[dtype] = first_column
                    # if (abs(vswr_column - freq_column) > 2) or (
                    #             abs(phase_column - freq_column) > 2):
                    #     sys.exit('Data Phase and VSWR are given from different sweeps - please'
                    #                  'check data file so first sweep has SWR and Phase info.')
                except:
                    sys.exit('Cannot find {dtype} data.'.format(dtype=dtype))
            # Only data is remaining.
            csv_reader = csv.reader(csvfile)

            rawdata = []
            for row in csv_reader:
                values = []  # order of data determined by dtypes list.
                for dtype in dtypes:
                    if dtype == 'phase_rad':
                        value = degrees_to_radians(float(row[dtype_to_column[
                            'phase_deg']]))
                    else:
                        value = float(row[dtype_to_column[dtype]])
                    values.append(value)
                rawdata.append((tuple(values)))
            rawdata = np.array(rawdata, dtype=array_dtypes)

            if k[0] == 'M' or k[0] == 'I':  # keys check out
                all_data[k] = rawdata
            else:
                sys.exit('There is an invalid key {}'.format(k))

            colour_dictionary[k] = hex_colors[0]
            hex_colors.remove(colour_dictionary[k])

    return all_data, colour_dictionary, missing_data, data_description


def degrees_to_radians(phase):

    phase_rad = float(phase) * math.pi / 180.0
    return phase_rad


def get_cable_loss_array(ref_freq_list, cable_length, cable_type):
    """
    Call the corresponding function depending on the cable type provided, then return 
    the dataset with cable loss.
    :param ref_freq_list:  list of frequencies to generate a numpy array for, given in Hz.
    :param cable_length: given in ft. 
    :param cable_type: the type of cable to create the cable loss dataset for. 
    :return: cable_loss_dataset, an array with dtypes freq (in Hz) and loss (in dB) 
    """
    if cable_type == 'Belden8237':
        cable_loss_dataset = create_belden_8237_cable_loss_array(ref_freq_list,
                                                                 cable_length)
    elif cable_type == 'Belden8214':
        cable_loss_dataset = create_belden_8214_cable_loss_array(ref_freq_list,
                                                                 cable_length)
    elif cable_type == 'Belden9913':
        cable_loss_dataset = create_belden_9913_cable_loss_array(ref_freq_list,
                                                                 cable_length)
    elif cable_type == 'LMR400':
        cable_loss_dataset = create_lmr400_cable_loss_array(ref_freq_list,
                                                                 cable_length)
    elif cable_type == 'C1180':
        cable_loss_dataset = create_carol_c1180_cable_loss_array(ref_freq_list,
                                                                 cable_length)
    else:
        raise Exception('No cable model set up for that cable type.')

    return cable_loss_dataset


def create_lmr400_cable_loss_array(ref_freq_list, cable_length):
    """
    Take a list of reference frequencies and cable length and return a numpy array with 
    dtypes 'freq' and 'loss' for LMR400 cable.
    :param ref_freq_list:  list of frequencies to generate a numpy array for, given in Hz.
    :param cable_length: given in ft. 
    :return: cable_loss_array, an array with dtypes freq (in Hz) and loss (in dB)
    """

    cable_loss = [cable_length/100.0 * (0.122290 * math.sqrt(freq * 10.0**-6) + 0.000260 *
                                      freq * 10.0**-6) for freq in ref_freq_list]

    cable_loss_array = []
    for freq, loss in zip(ref_freq_list, cable_loss):
        cable_loss_array.append((freq, loss))
    cable_loss_array = np.array(cable_loss_array, dtype=[('freq', 'i4'), ('loss', 'f4')])
    return cable_loss_array


def create_belden_8214_cable_loss_array(ref_freq_list, cable_length):
    """
    Take a list of reference frequencies and cable length and return a numpy array with 
    dtypes 'freq' and 'loss' for Belden 8214 RG8 cable.
    :param ref_freq_list:  list of frequencies to generate a numpy array for, given in Hz.
    :param cable_length: given in ft. 
    :return: cable_loss_array, an array with dtypes freq (in Hz) and loss (in dB)
    """

    # do a log-log fit with given values from datasheet:
    # 1 MHz: 0.1 dB/100ft
    # 10 MHz: 0.5 dB/100ft
    # 50 MHz: 1.2 dB/100ft
    # log(y) = slope * log(x) + intercept
    slope_1 = math.log(0.5/0.1, 10.0) / math.log(10.0/1.0, 10.0)
    slope_2 = math.log(1.2/0.5, 10.0) / math.log(50.0/10.0, 10.0)
    intercept = math.log(0.1, 10.0) - slope_1 * math.log(1.0, 10.0)

    print('Slopes: {slope_1}, {slope_2}'.format(slope_1=slope_1, slope_2=slope_2))

    cable_loss = [cable_length/100.0 * 10.0 ** (slope_1 * math.log(freq * 10**-6, 10.0) +
                  intercept) for freq in ref_freq_list if freq <= 10000000]
    cable_loss_2 = [cable_length/100.0 * 10.0 ** (slope_2 * math.log(freq * 10**-6, 10.0) +
                    intercept) for freq in ref_freq_list if freq > 10000000]
    cable_loss.extend(cable_loss_2)

    cable_loss_array = []
    for freq, loss in zip(ref_freq_list, cable_loss):
        cable_loss_array.append((freq, loss))
    cable_loss_array = np.array(cable_loss_array, dtype=[('freq', 'i4'), ('loss', 'f4')])
    return cable_loss_array


def create_belden_9913_cable_loss_array(ref_freq_list, cable_length):
    """
    Take a list of reference frequencies and cable length and return a numpy array with 
    dtypes 'freq' and 'loss' for Belden 9913 RG8/U cable.
    :param ref_freq_list:  list of frequencies to generate a numpy array for, given in Hz.
    :param cable_length: given in ft. 
    :return: cable_loss_array, an array with dtypes freq (in Hz) and loss (in dB)
    """

    # do a log-log fit with given values from datasheet:
    # 5 MHz: 1.312 dB/100m
    # 10 MHz: 1.641 dB/100m
    # 50 MHz: 3.281 dB/100m
    # log(y) = slope * log(x) + intercept
    slope_1 = math.log(1.641/1.312, 10.0) / math.log(10.0/5.0, 10.0)
    slope_2 = math.log(3.281/1.641, 10.0) / math.log(50.0/10.0, 10.0)
    intercept = math.log(1.312, 10.0) - slope_1 * math.log(5.0, 10.0)

    print('Slopes: {slope_1}, {slope_2}'.format(slope_1=slope_1, slope_2=slope_2))

    cable_length = cable_length/3.2808  # convert to metres because these attenuation
    # values are in metres.

    cable_loss = [cable_length/100.0 * 10.0 ** (slope_1 * math.log(freq * 10**-6, 10.0) +
                  intercept) for freq in ref_freq_list if freq <= 10000000]
    cable_loss_2 = [cable_length/100.0 * 10.0 ** (slope_2 * math.log(freq * 10**-6, 10.0) +
                    intercept) for freq in ref_freq_list if freq > 10000000]
    cable_loss.extend(cable_loss_2)

    cable_loss_array = []
    for freq, loss in zip(ref_freq_list, cable_loss):
        cable_loss_array.append((freq, loss))
    cable_loss_array = np.array(cable_loss_array, dtype=[('freq', 'i4'), ('loss', 'f4')])
    return cable_loss_array


def create_belden_8237_cable_loss_array(ref_freq_list, cable_length):
    """
    Take a list of reference frequencies and cable length and return a numpy array with 
    dtypes 'freq' and 'loss' for Belden 8237 RG8/U cable.
    :param ref_freq_list:  list of frequencies to generate a numpy array for, given in Hz.
    :param cable_length: given in ft. 
    :return: cable_loss_array, an array with dtypes freq (in Hz) and loss (in dB)
    """

    # do a log-log fit with given values from datasheet:
    # 1 MHz: 0.2 dB/100ft
    # 10 MHz: 0.6 dB/100ft
    # 50 MHz: 1.3 dB/100ft
    # log(y) = slope * log(x) + intercept
    slope_1 = math.log(0.6/0.2, 10.0) / math.log(10.0/1.0, 10.0)
    slope_2 = math.log(1.3/0.6, 10.0) / math.log(50.0/10.0, 10.0)
    intercept = math.log(0.2, 10.0) - slope_1 * math.log(1.0, 10.0)

    print('Slopes: {slope_1}, {slope_2}'.format(slope_1=slope_1, slope_2=slope_2))
    cable_loss = [cable_length/100.0 * (10.0 ** (slope_1 * math.log(freq * 10.0**-6,
                                                                   10.0) +
                  intercept)) for freq in ref_freq_list if freq <= 10000000]
    cable_loss_2 = [cable_length/100.0 * (10.0 ** (slope_2 * math.log(freq * 10.0**-6,
                                                                   10.0) +
                    intercept)) for freq in ref_freq_list if freq > 10000000]
    cable_loss.extend(cable_loss_2)

    cable_loss_array = []
    for freq, loss in zip(ref_freq_list, cable_loss):
        cable_loss_array.append((freq, loss))
    cable_loss_array = np.array(cable_loss_array, dtype=[('freq', 'i4'), ('loss', 'f4')])
    return cable_loss_array


def create_carol_c1180_cable_loss_array(ref_freq_list, cable_length):
    """
    Take a list of reference frequencies and cable length and return a numpy array with 
    dtypes 'freq' and 'loss' for Carol C1180 (General Cable) RG8/U cable.
    :param ref_freq_list:  list of frequencies to generate a numpy array for, given in Hz.
    :param cable_length: given in ft. 
    :return: cable_loss_array, an array with dtypes freq (in Hz) and loss (in dB)
    """

    # do a log-log fit with given values from datasheet:
    # 1 MHz: 0.13 dB/100ft
    # 10 MHz: 0.4 dB/100ft
    # 50 MHz: 0.9 dB/100ft
    # log(y) = slope * log(x) + intercept
    slope_1 = math.log(0.4/0.13, 10.0) / math.log(10.0/1.0, 10.0)
    slope_2 = math.log(0.9/0.4, 10.0) / math.log(50.0/10.0, 10.0)
    intercept = math.log(0.13, 10.0) - slope_1 * math.log(1.0, 10.0)

    print('Slopes: {slope_1}, {slope_2}'.format(slope_1=slope_1, slope_2=slope_2))
    cable_loss = [cable_length/100.0 * (10.0 ** (slope_1 * math.log(freq * 10.0**-6,
                                                                   10.0) +
                  intercept)) for freq in ref_freq_list if freq <= 10000000]
    cable_loss_2 = [cable_length/100.0 * (10.0 ** (slope_2 * math.log(freq * 10.0**-6,
                                                                   10.0) +
                    intercept)) for freq in ref_freq_list if freq > 10000000]
    cable_loss.extend(cable_loss_2)

    cable_loss_array = []
    for freq, loss in zip(ref_freq_list, cable_loss):
        cable_loss_array.append((freq, loss))
    cable_loss_array = np.array(cable_loss_array, dtype=[('freq', 'i4'), ('loss', 'f4')])
    return cable_loss_array


def vswr_to_receive_power(data, cable_loss_array):
    """
    Take in a numpy array with vswr dtype and return a numpy array with both vswr and 
    return_db dtype.
    :param: data: numpy array with vswr dtype.
    :param: cable_loss: array of cable loss for the same frequencies as in data. 
    :return: 
    """
    new_data = []

    # Check if both data and cable have the same values for frequency.
    if not np.array_equal(data['freq'], cable_loss_array['freq']):
        sys.exit('Frequencies do not match in datasets - exiting')

    dtypes = [(x, str(y[0])) for x, y in sorted(data.dtype.fields.items(), key=lambda
        k: k[1])] # get list of dtypes sorted by column

    for num, entry in enumerate(data):
        try:
            VSWR = entry['vswr']
            cable_loss = cable_loss_array['loss'][num]
        except:
            raise Exception('No vswr dtype in this array.')

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
            print("WRONG - we have no power at the balun")
            print("This would suggest your cable loss model is too lossy.")
            print("Cable loss = {loss} db at {freq}".format(loss=cable_loss,freq=entry[
                'freq']))
            sys.exit()
        reflection_db_at_balun = 10 * math.log((w_reflected_at_balun /
                                                power_reaching_balun_w), 10)
        transmission_db_at_balun = 10 * math.log(w_transmitted_at_balun /
                                                 power_reaching_balun_w, 10)

        # ASSUMING we have a symmetrical mismatch point at the balun and transmission
        # S12 = S21.
        # power incoming from antenna will have mismatch point and then cable losses.
        receive_power = transmission_db_at_balun - cable_loss
        receive_power = round(receive_power, 5)
        list_of_values_per_freq = []
        for num, dtype in enumerate(dtypes):
            list_of_values_per_freq.append(entry[num])
        list_of_values_per_freq.append(receive_power)
        new_data.append(tuple(list_of_values_per_freq))

    dtypes.append(('return_db', 'float32'))
    new_data = np.array(new_data, dtype=dtypes)
    return new_data
