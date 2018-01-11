import numpy as np
import math
import sys
from scipy import stats
import random


def unwrap_phase(data):  # TODO fix up so returns separate data
    # take a numpy array with phase_deg and phase_rad datatypes and unwrap.
    try:
        assert 'phase' in data.dtype.names or 'phase_deg' in data.dtype.names or 'phase_rad' in data.dtype.names
    except:
        raise Exception('Cannot Find Phase Dtype to Wrap in Numpy Array')
    new_data = np.copy(data)
    if 'phase_deg' in data.dtype.names:
        if max(data['phase_deg']) < 180.0 and min(data['phase_deg']) > -180.0:
            for num, entry in enumerate(data['phase_deg']):
                if entry > 300.0 + data['phase_deg'][num - 1]:
                    for i in range(num, len(data)):
                        new_data['phase_deg'][i] = data['phase_deg'][i] - 360.0
                elif entry < -300.0 + data['phase_deg'][num - 1]:
                    for i in range(num, len(data)):
                        new_data['phase_deg'][i] = data['phase_deg'][i] + 360.0
    if 'phase' in data.dtype.names:
        if max(data['phase']) < 180.0 and min(data['phase']) > -180.0:
            for num, entry in enumerate(data['phase']):
                if entry > 300.0 + data['phase'][num - 1]:
                    for i in range(num, len(data)):
                        new_data['phase'][i] = data['phase'][i] - 360.0
                elif entry < -300.0 + data['phase'][num - 1]:
                    for i in range(num, len(data)):
                        new_data['phase'][i] = data['phase'][i] + 360.0
    if 'phase_rad' in data.dtype.names:
        if max(data['phase_rad']) < math.pi and min(data['phase_rad']) > -math.pi:
            for num, entry in enumerate(data['phase_rad']):
                if entry > (300.0 * math.pi / 180.0) + data['phase_rad'][num - 1]:
                    for i in range(num, len(data)):
                        new_data['phase_rad'][i] = data['phase_rad'][i] - 2 * math.pi
                elif entry < -(300.0 * math.pi / 180.0) + data['phase_rad'][num - 1]:
                    for i in range(num, len(data)):
                        new_data['phase_rad'][i] = data['phase_rad'][i] + 2 * math.pi

    return new_data


def wrap_phase(data):
    """
    Take a numpy array with dtype of phase, phase_deg, or phase_rad and wrap the phase.
    """
    try:
        assert 'phase' in data.dtype.names or 'phase_deg' in data.dtype.names or 'phase_rad' in data.dtype.names
    except:
        raise Exception('Cannot Find Phase Dtype to Wrap in Numpy Array')

    new_data = np.copy(data)
    if 'phase' in data.dtype.names:
        if max(data['phase']) > 180.0 or min(data['phase']) < -180.0:
            for num, entry in enumerate(new_data['phase']):
                if entry > 180.0:
                    for i in range(num, len(new_data)):
                        new_data['phase'][i] = new_data['phase'][i] - 360.0
                elif entry < -180.0:
                    for i in range(num, len(new_data)):
                        new_data['phase'][i] = new_data['phase'][i] + 360.0
    if 'phase_deg' in data.dtype.names:
        if max(data['phase_deg']) > 180.0 or min(data['phase_deg']) < -180.0:
            for num, entry in enumerate(new_data['phase_deg']):
                if entry > 180.0:
                    for i in range(num, len(new_data)):
                        new_data['phase_deg'][i] = new_data['phase_deg'][i] - 360.0
                elif entry < -180.0:
                    for i in range(num, len(new_data)):
                        new_data['phase_deg'][i] = new_data['phase_deg'][i] + 360.0
    if 'phase_rad' in data.dtype.names:
        if max(data['phase_rad']) > math.pi or min(data['phase_rad']) < -math.pi:
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


def check_frequency_array(dict_of_arrays_with_freq_dtype, min_dataset_length, freqs=None):
    """
    Check dictionary where values are numpy arrays (1-dimensional, multiple dtypes with one dtype 
    being 'freq'). Check that the arrays are of the same length. If they are of lengths that are 
    multiples, make the frequency values equal by removing the multiples and making all arrays the 
    minimum dataset length. If they are not multiples, return an error. pass in an array of only
    dtype 'freq' if you want to also check that the frequencies are the same as some reference 
    frequency array.
    :param dict_of_arrays_with_freq_dtype: 
    :param min_dataset_length: 
    :param freqs: a reference frequency array, if None then will use the frequency of the first 
        short dataset.
    :return: dict_of_arrays_with_freq_dtype, where all arrays are of same length.
    """
    short_datasets = []
    long_datasets = {}
    for ant, dataset in dict_of_arrays_with_freq_dtype.items():
        if len(dataset) == min_dataset_length:
            short_datasets.append(ant)
        else:
            long_datasets[ant] = len(dataset)

    if freqs is None:
        reference_frequency = dict_of_arrays_with_freq_dtype[short_datasets[0]]['freq']
    else:
        reference_frequency = freqs

    for ant in short_datasets:
        for value, entry in enumerate(dict_of_arrays_with_freq_dtype[ant]):
            if entry['freq'] != reference_frequency[value]:
                sys.exit('Frequencies do not match in datasets - exiting')

    for ant, length in long_datasets.items():
        lines_to_delete = []
        if length % min_dataset_length == 0:
            integer = length/min_dataset_length
            for value, entry in enumerate(dict_of_arrays_with_freq_dtype[ant]):
                if (value-1) % integer != 0:
                    #print entry['freq']
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


def correct_frequency_array(dict_of_arrays_with_freq_dtype):
    """
    Make all arrays in the dictionary the same length and with the same array as the 'freq' dtype,
    using linear interpolation for all dtypes except the 'freq' dtype. This returns all datasets 
    with length equal to the max dataset length (as long as max dataset starts at the latest freq)
    :param dict_of_arrays_with_freq_dtype: 
    :return: dict_of_arrays_with_freq_dtype, where all arrays are the same length.
    """

    # find latest starting frequency
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

    while dict_of_arrays_with_freq_dtype[max_array]['freq'][0] < latest_starting_freq:
        dict_of_arrays_with_freq_dtype[max_array] = \
            np.delete(dict_of_arrays_with_freq_dtype[max_array], (0), axis=0)

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
            new_dict_of_arrays[path][dtype] = np.interp(reference_frequency_array, array['freq'], array[dtype])

    return new_dict_of_arrays


def get_slope_of_phase_in_nano(phase_data, freq_hz):  # TODO check this
    """
    This was an attempt to get time data across frequency by differentiating phase as it is somewhat
    non-linear. Did not provide good results so no longer in use. 
    :param phase_data: rads
    :param freq_hz: Hz
    :return: array of time(ns) based on differentiation of phase near datapoint.
    """

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


def combine_arrays(array_dict):  # TODO check this
    """
    Combine arrays with the same 'freq' dtype array by adding all arrays in the dictionary into one 
    numpy array. Input dictionary value arrays need a phase_rad dtype and a magnitude dtype at this time.
    :param array_dict: 
    :return: combined_array
    """
    one_array_key = random.choice(array_dict.keys())

    for k, v in array_dict.items():
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

    combined_array = unwrap_phase(combined_array)
    return combined_array


def reflection_to_transmission_phase(data):
    """
    Return the phase values halved.
    :param data: 
    :return: 
    """

    data = unwrap_phase(data) # needs to be a phase-unwrapped dataset.

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
