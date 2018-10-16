import numpy as np
import math
import sys
from scipy import stats
import random


def unwrap_phase(data):
    """
    Take a numpy array with phase, phase_deg, and/or phase_rad datatypes and unwrap.
    :param data: a numpy array
    :return: a new array with unwrapped phase, phase_deg, and/or phase_rad dtypes
    """
    try:
        assert 'phase' in data.dtype.names or 'phase_deg' in data.dtype.names or \
               'phase_rad' in data.dtype.names
    except:
        raise Exception('Cannot Find Phase Dtype to Wrap in Numpy Array')

    # If there is a jump from one datapoint to the next of more than 250 degrees,
    # we will assume it is a wrap (there was a 360 degree jump between the datapoints). It
    # may be this low due to a large slope in the line (if the path is long)

    new_data = np.copy(data)
    if 'phase_deg' in data.dtype.names:
        if np.amax(data['phase_deg']) < 180.0 and np.amin(data['phase_deg']) > -180.0:
            for num, entry in enumerate(data['phase_deg']):
                if entry > 250.0 + data['phase_deg'][num - 1]:
                    for i in range(num, len(data)):
                        new_data['phase_deg'][i] -= 360.0
                elif entry < -250.0 + data['phase_deg'][num - 1]:
                    for i in range(num, len(data)):
                        new_data['phase_deg'][i] += 360.0
    if 'phase' in data.dtype.names:
        if np.amax(data['phase']) < 180.0 and np.amin(data['phase']) > -180.0:
            for num, entry in enumerate(data['phase']):
                if entry > (250.0 + data['phase'][num - 1]):
                    for i in range(num, len(new_data)):
                        new_data['phase'][i] -= 360.0
                elif entry < (-250.0 + data['phase'][num - 1]):
                    for i in range(num, len(new_data)):
                        new_data['phase'][i] += 360.0
    if 'phase_rad' in data.dtype.names:
        if np.amax(data['phase_rad']) < math.pi and np.amin(data['phase_rad']) > -math.pi:
            for num, entry in enumerate(data['phase_rad']):
                if entry > (250.0 * math.pi / 180.0) + data['phase_rad'][num - 1]:
                    for i in range(num, len(data)):
                        new_data['phase_rad'][i] -= 2 * math.pi
                elif entry < -(250.0 * math.pi / 180.0) + data['phase_rad'][num - 1]:
                    for i in range(num, len(data)):
                        new_data['phase_rad'][i] += 2 * math.pi

    return new_data


def wrap_phase(data):
    """
    Take a numpy array with dtype of phase, phase_deg, or phase_rad and wrap the phase.
    :param data: a numpy array
    :return: a new array with wrapped phase, phase_deg, and/or phase_rad dtypes
    """
    try:
        assert 'phase' in data.dtype.names or 'phase_deg' in data.dtype.names or 'phase_rad' in data.dtype.names
    except:
        raise Exception('Cannot Find Phase Dtype to Wrap in Numpy Array')

    # Confine the phase within 180 degrees to -180 degrees to wrap it.

    new_data = np.copy(data)
    if 'phase' in data.dtype.names:
        if np.amax(data['phase']) > 180.0 or np.amin(data['phase']) < -180.0:
            for num, entry in enumerate(new_data['phase']):
                if entry > 180.0:
                    for i in range(num, len(new_data)):
                        new_data['phase'][i] = new_data['phase'][i] - 360.0
                elif entry < -180.0:
                    for i in range(num, len(new_data)):
                        new_data['phase'][i] = new_data['phase'][i] + 360.0
    if 'phase_deg' in data.dtype.names:
        if np.amax(data['phase_deg']) > 180.0 or np.amin(data['phase_deg']) < -180.0:
            for num, entry in enumerate(new_data['phase_deg']):
                if entry > 180.0:
                    for i in range(num, len(new_data)):
                        new_data['phase_deg'][i] = new_data['phase_deg'][i] - 360.0
                elif entry < -180.0:
                    for i in range(num, len(new_data)):
                        new_data['phase_deg'][i] = new_data['phase_deg'][i] + 360.0
    if 'phase_rad' in data.dtype.names:
        if np.amax(data['phase_rad']) > math.pi or np.amin(data['phase_rad']) < -math.pi:
            for num, entry in enumerate(new_data['phase_rad']):
                if entry > math.pi:
                    for i in range(num, len(new_data)):
                        new_data['phase_rad'][i] = new_data['phase_rad'][i] - 2 * math.pi
                elif entry < -math.pi:
                    for i in range(num, len(new_data)):
                        new_data['phase_rad'][i] = new_data['phase_rad'][i] + 2 * math.pi
    return new_data


def wrap_phase_dictionary(dict_with_freq_and_phase):
    """
    Take a dictionary with values that are numpy arrays with dtypes of freq and any of phase,
    phase_deg, or phase_rad and wrap all values in the dictionary. 
    :param dict_with_freq_and_phase: 
    :return: dictionary with all values of numpy arrays having phase wrapped.
    """
    new_dict = {}
    for ant, dataset in dict_with_freq_and_phase.items():
        wrapped_dataset = wrap_phase(dataset)
        new_dict[ant] = wrapped_dataset

    return new_dict


def reduce_frequency_array(dict_of_arrays_with_freq_dtype,freqs=None):
    """
    Check a dictionary where values are numpy arrays (multiple dtypes with one dtype
    being 'freq'). Check that the arrays are of the same length. If they are of lengths
    that are multiples, make the frequency values equal by removing the extra points
    and making all arrays the minimum dataset length. If they are not multiples,
    return an error.

    This is useful because sometimes site-recorded datasets were recorded with a
    different number of points (200, 400, 800) over the same frequency spectrum. To be
    able to compare these datasets and combine datasets into a single array, this function
    will make all datasets equal to the minimum length given by removing the points in
    between.

    Pass in 'freqs', an array of only dtype 'freq' if you want to also check that the
    frequencies are the same as some reference frequency array.

    :param dict_of_arrays_with_freq_dtype: dictionary where each value is a
    numpy array that represents a path over the frequency spectrum, having a dtype
    name of 'freq'. Other dtypes common are for phase (phase_rad, phase_deg) and
    magnitude, but they are not necessary; the other dtypes can be anything and the
    values will be populated to preserve the data recorded across frequency.
    :param freqs: a reference frequency array, if None then will use the frequency of the
        first shortest dataset found in the dictionary.
    :return: dict_of_arrays_with_freq_dtype, where all arrays are of same length.
    """

    # get the minimum dataset length of datasets in the dictionary in case the data was
    # recorded using a different number of points.
    min_dataset_length = get_min_dataset_length(dict_of_arrays_with_freq_dtype)

    short_dataset_keys = []  # list of keys with the minimum dataset length
    long_datasets = {}
    for ant, dataset in dict_of_arrays_with_freq_dtype.items():
        if len(dataset) == min_dataset_length:
            short_dataset_keys.append(ant)
        else:
            long_datasets[ant] = len(dataset)

    if freqs is None:
        reference_frequency = dict_of_arrays_with_freq_dtype[short_dataset_keys[0]]['freq']
    else:
        reference_frequency = freqs

    # Check if all the short datasets have the same values for frequency.
    for ant in short_dataset_keys:
        for index, entry in enumerate(dict_of_arrays_with_freq_dtype[ant]):
            #print(entry['freq'] - reference_frequency[value])
            if not np.array_equal(entry['freq'], reference_frequency[index]):
                sys.exit('Frequencies do not match in datasets - exiting')

    for ant, length in long_datasets.items():
        lines_to_delete = []
        if length % min_dataset_length == 0:
            integer = length/min_dataset_length
            for value, entry in enumerate(dict_of_arrays_with_freq_dtype[ant]):
                if (value-1) % integer != 0:
                    lines_to_delete.append(value)
                elif entry['freq'] != reference_frequency[(value-1)/integer]:
                    sys.exit('Datasets are in multiple lengths but frequency axis '
                              'values are not the same when divided, length {} broken down to length '
                              '{}'.format(length, min_dataset_length))
            dict_of_arrays_with_freq_dtype[ant] = np.delete(dict_of_arrays_with_freq_dtype[ant], lines_to_delete, axis=0)
        else:
            sys.exit('Please ensure datasets are the same length and frequency axes '
                     'are the same, length {} is greater than minimum dataset length '
                     '{}'.format(length, min_dataset_length))

    return dict_of_arrays_with_freq_dtype


def interp_frequency_array(dict_of_arrays_with_freq_dtype):
    """
    Make all arrays in the dictionary the same length, and make all arrays in the
    dictionary have the same elements for the 'freq' dtype.

    This is done using linear interpolation for all dtypes except the 'freq' dtype. This
    returns all datasets  with the maximum dataset length possible with interpolation,
    from the highest start frequency in any of the datasets, to the lowest end
    frequency in any of the datasets.

    :param dict_of_arrays_with_freq_dtype: dictionary where each value is a
    numpy array that represents a path over the frequency spectrum, having a dtype
    name of 'freq'. Other dtypes common are for phase (phase_rad, phase_deg) and
    magnitude, but they are not necessary; the other dtypes can be anything and the
    values will be populated to preserve the data recorded across frequency.
    :return: dict_of_arrays_with_freq_dtype, where all arrays are the same length.
    """

    # find latest starting frequency and earliest end frequency of the arrays in the dict.
    latest_starting_freq = 0
    earliest_ending_freq = 10000000000
    max_data_points = 0
    for path, array in dict_of_arrays_with_freq_dtype.items():
        if array['freq'][0] > latest_starting_freq:
            latest_starting_freq = array['freq'][0]
        if array['freq'][-1] < earliest_ending_freq:
            earliest_ending_freq = array['freq'][-1]
        if array.shape[0] > max_data_points:
            max_data_points = array.shape[0]
            max_array = path

    # Delete frequencies lower than the latest starting frequency in what will be the
    # reference frequency array.
    while dict_of_arrays_with_freq_dtype[max_array]['freq'][0] < latest_starting_freq:
        dict_of_arrays_with_freq_dtype[max_array] = \
            np.delete(dict_of_arrays_with_freq_dtype[max_array], (0), axis=0)

    # Delete frequencies higher than the earliest ending frequency in the reference
    # frequency array.
    while dict_of_arrays_with_freq_dtype[max_array]['freq'][-1] > earliest_ending_freq:
        dict_of_arrays_with_freq_dtype[max_array] = \
            np.delete(dict_of_arrays_with_freq_dtype[max_array], (-1), axis=0)

    len_of_new_arrays = dict_of_arrays_with_freq_dtype[max_array].shape[0]
    reference_frequency_array = dict_of_arrays_with_freq_dtype[max_array]['freq']

    new_dict_of_arrays = {}

    for path, array in dict_of_arrays_with_freq_dtype.items():
        new_dict_of_arrays[path] = np.zeros(len_of_new_arrays, dtype=array.dtype)
        new_dict_of_arrays[path]['freq'] = reference_frequency_array
        for dtype in array.dtype.names:
            new_dict_of_arrays[path][dtype] = np.interp(reference_frequency_array,
                                                        array['freq'], array[dtype])

    return new_dict_of_arrays


def get_slope_of_phase_in_nano(phase_data, freq_hz):
    """
    This was an attempt to get time data across frequency by differentiating phase as it
    is somewhat non-linear. Did not provide good results so not in use but could be
    revisited in the future.
    :param phase_data: rads
    :param freq_hz: Hz
    :return: array of time(ns) based on differentiation of phase near datapoint.
    """

    # dy = np.diff(dataset['phase_rad']) * -1e9 / dx
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
        dy.append(tslope * -1e9)

    dy = np.array(dy)

    return dy


def combine_arrays(array_dict):  # TODO check this
    """
    Combine arrays with the same 'freq' dtype array by adding all arrays in the dictionary
    elementwise into one numpy array. Input dictionary value arrays need a phase_rad dtype
    and a magnitude dtype at this time.

    :param array_dict: dictionary where each value is a numpy array that represents a
    path over the frequency spectrum, having dtypes 'freq' (frequency), magnitude,
    and phase_rad.
    :return: combined_array, with unwrapped phase values. This is the result of summing
    together all the numpy arrays in the array_dict. This will have a length equal to
    to the length of the arrays in the array_dict and will have three dtypes: 'freq',
    'magnitude', 'phase_rad', and 'phase_deg'.
    """

    # Get a random key from the dictionary to verify that all dictionaries have the same
    # frequency array.
    one_array_key = random.choice(list(array_dict.keys()))

    for k, v in array_dict.items():
        for a, b in zip(array_dict[one_array_key], v):
            if a['freq'] != b['freq']:
                errmsg = "Frequencies not Equal {} {}".format(a['freq'], b['freq'])
                sys.exit(errmsg)

    combined_array = np.copy(array_dict[one_array_key])

    for k, v in array_dict.items():
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

    combined_array = unwrap_phase(combined_array)
    return combined_array


def vswr_to_single_receive_direction(data, cable_loss_array):
    """
    Take in a numpy array with vswr dtype and return a numpy array with both vswr and
    magnitude dtype. This magnitude is a single direction magnitude, indicating the dB
    loss that would occur from the signal incident at the antenna to the end of the
    feedline.

    Also convert the phase from a reflected phase value to a single direction
    transmission value, using the reflection_to_transmission_phase function.

    :param: data: numpy array with freq and vswr dtype, and one or more of the phase
     dtypes ('phase', 'phase_deg', or 'phase_rad')
    :param: cable_loss: array of cable loss for the same frequencies as in data.
    :return: new_data: numpy array with vswr dtype and magnitude dtype, where magnitude
     is the S12 magnitude, and where the phase is the S12 phase (single direction).
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

        watts_incident_at_balun = 10 ** (-1 * cable_loss / 10)
        # get single-direction data by making the power base equal to the watts
        # incident at the balun.

        dB_reflected_at_balun = -1 * return_loss_dB + cable_loss

        watts_reflected_at_balun = 10 ** (dB_reflected_at_balun / 10)

        watts_transmitted_at_balun = watts_incident_at_balun - watts_reflected_at_balun
        if watts_transmitted_at_balun <= 0:
            print("WRONG - we have no power at the balun")
            print("This would suggest your cable loss model is too lossy.")
            print("Cable loss = {loss} db at {freq}".format(loss=cable_loss,freq=entry[
                'freq']))
            # TODO error?

        reflection_db_at_balun = 10 * math.log((watts_reflected_at_balun /
                                                watts_incident_at_balun), 10)
        transmission_db_at_balun = 10 * math.log(watts_transmitted_at_balun /
                                                 watts_incident_at_balun, 10)

        # ASSUMING we have a symmetrical mismatch point at the balun and transmission
        # S12 = S21, so transmission_db_at_balun out = the received dB at balun on
        # receive path.
        # Incoming power from antenna will have mismatch point and then cable losses.
        receive_power = transmission_db_at_balun - cable_loss
        receive_power = round(receive_power, 5)
        list_of_values_per_freq = []
        for num, dtype in enumerate(dtypes):
            list_of_values_per_freq.append(entry[num])
        list_of_values_per_freq.append(receive_power)
        new_data.append(tuple(list_of_values_per_freq))

    dtypes.append(('magnitude', 'float32'))
    new_data = np.array(new_data, dtype=dtypes)

    # We now have single direction magnitude, but also need single direction phase.
    # Wrapping then unwrapping ensures there is no 360 degree offset from one dataset
    # to another. (All datasets will start with a phase between -180 to 180 degrees at
    # the lowest frequency in the spectrum).
    new_data = unwrap_phase(new_data)
    # convert phase to single direction - unwraps within function.
    dataset_with_transmission_data = reflection_to_transmission_phase(new_data)

    return dataset_with_transmission_data


def reflection_to_transmission_phase(incoming_data):
    """
    Return the phase values halved. If we assume S12 and S21 are the same at the balun,
    we can make this approximation that S21 phase = S11 phase / 2. We can assume that
    the transmitted power T12 will be equal to (incident power - cable losses on
    incident)- (S11 (reflected power) + cable losses on reflect)

    :param incoming_data: a numpy array that you would like to halve the phase value
    of. This is done to attempt to get a S12 value from an S11 measurement. This is done
    under the assumption that S12 = S21 at a single reflection point at the end of the
    path (for SuperDARN antenna/feedline paths, this is at the balun).
    :return: new_data: data with phase values adjusted to be a single direction.
    """

    data = unwrap_phase(incoming_data)  # needs to be a phase-unwrapped dataset.

    try:
        assert 'phase' in data.dtype.names or 'phase_deg' in data.dtype.names or 'phase_rad' in data.dtype.names
    except:
        raise Exception('Cannot Find Phase Dtype to Wrap in Numpy Array')

    new_data = np.copy(data)
    if 'phase' in data.dtype.names:
        new_data['phase'] = np.true_divide(new_data['phase'], 2.0)
    if 'phase_deg' in data.dtype.names:
        new_data['phase_deg'] = np.true_divide(new_data['phase_deg'], 2.0)
    if 'phase_rad' in data.dtype.names:
        new_data['phase_rad'] = np.true_divide(new_data['phase_rad'], 2.0)
    return new_data


def get_min_dataset_length(data_dict):
    """
    Get the minimum dataset length of all datasets in a dictionary. This is necessary
    to enforce all datasets to the same length (with same frequency values) in order to do
    operations elementwise. If they aren't the same length, we can remove points or do
    interpolation to make them the same length.

    :param data_dict: a dictionary where values are numpy arrays representing a phase
    path of some kind.
    :return: the minimum dataset length of all arrays in the dictionary. This is the
    shape[0] value of the array, as there can be multiple dtypes in the array.
    """
    min_dataset_length = 10000000000
    for path, dataset in data_dict.items():
        if len(dataset) < min_dataset_length:
            min_dataset_length = len(dataset)
    return min_dataset_length


def create_linear_fit_dictionary(array):
    """
    Get the line of best fit for a given numpy array with phase data over a frequency
    spectrum. Also get the offset of the actual data from the line of best fit across
    the spectrum.

    :param array: a numpy array with 'freq' and 'phase_rad' dtypes.
    :return: data_array_linear_fit_dict: a dictionary with information on the line of
    best fit and the data's offset from that line. Includes the keys 'slope',
    'intercept', 'rvalue', 'pvalue', 'stderr', 'offset_of_best_fit_rads' (a numpy array
    of the difference between data and line of best fit), 'time_delay_ns' (the time
    delay value for the given slope of the line of best fit), and 'best_fit_line_rads'
    (the numpy array of the line of best fit data).

    """
    data_array = unwrap_phase(array)

    # In this fit, slope represents the change in phase over frequency. This can be
    # used to calculate the speed of the wave through the medium or the time for the
    # wave to move through the medium. The intercept is theoretical here and used to
    # get the line so that we can determine how good the assumption is that this path is
    # linear.

    slope, intercept, rvalue, pvalue, stderr = stats.linregress(data_array['freq'],
                                                                data_array['phase_rad'])
    offset_of_best_fit = []
    best_fit_line = []
    for entry in data_array:
        # This is the value of the line at this point.
        best_fit_value = slope * entry['freq'] + intercept
        best_fit_line.append(best_fit_value)
        # This is the offset of the actual data from that line.
        offset_of_best_fit.append(entry['phase_rad'] - best_fit_value)

    # Convert both lists to numpy arrays and wrap the phase data.
    best_fit_line = np.array(best_fit_line, dtype=[('phase_rad', 'f4')])
    best_fit_line = wrap_phase(best_fit_line)
    offset_of_best_fit = np.array(offset_of_best_fit, dtype=[('phase_rad', 'f4')])
    offset_of_best_fit = wrap_phase(offset_of_best_fit)

    data_array_linear_fit_dict = {'slope': slope, 'intercept': intercept, 'rvalue':
                                  rvalue, 'pvalue': pvalue, 'stderr': stderr,
                                  'offset_of_best_fit_rads':
                                  offset_of_best_fit['phase_rad'], 'time_delay_ns':
                                  round(slope / (2 * math.pi), 11) * -1e9,
                                  'best_fit_line_rads': best_fit_line}

    return data_array_linear_fit_dict
