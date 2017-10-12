#!/usr/bin/python

# Phase_diff.py
# To measure the phase offset in cables, antennas
# using S11 phase measurements and VSWR. Approximate
# S12 phase change at the antenna is found assuming S12 = S21.
# We then plot the estimated phase change at the end of the feedline
# Simply due to feedline and antenna disparities.

import sys
import time
import math
import numpy as np
import matplotlib.pyplot as plt
import json
# General variables to change depending on data being used
radar_name = sys.argv[1]
data_location = sys.argv[2]
plot_location = sys.argv[3]
vswr_main_files_str = sys.argv[4]
vswr_intf_files_str = sys.argv[5]

S12_arrays_plot_title = radar_name + ' Combined Main and IF Arrays \nAntenna/Feedlines'
data_description = 'This data was taken on site visits in August 2017.'

number_of_data_points = 801

sys.path.append(data_location)

with open(vswr_main_files_str) as f:
    vswr_main_files = json.load(f)
    #converting string keys to int keys
    for k in vswr_main_files.keys():
        vswr_main_files[int(k)] = vswr_main_files[k]
        del vswr_main_files[k]

with open(vswr_intf_files_str) as f:
    vswr_intf_files = json.load(f)
    #converting string keys to int keys
    for k in vswr_intf_files.keys():
        vswr_intf_files[int(k)] = vswr_intf_files[k]
        del vswr_intf_files[k]




# if we assume S12 and S21 are the same (safe for feedlines/antennas only)
# We can assume that S21 phase is S11 phase/2
# We can assume that the transmitted power T12 will be equal to (incident power - cable losses on
# incident)- (S11 (reflected power) + cable losses on reflect)



# estimated cable losses (LMR-400) @ 0.7 db/100ft * 600ft
cable_loss = 3.5  # in dB

main_data = {}
intf_data = {}

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
    for i in vswr_main_files.keys():
        with open(data_location + vswr_main_files[i], 'r') as csvfile:
            lines = csvfile.readlines()
            for ln in lines:
                if ln.find('Freq. [Hz]') != -1:  # found the right line
                    header_line = ln
                    break
            find_phase = header_line.split(",", 16)
            # print find_phase
            freq_column = find_phase.index('Freq. [Hz]')
            vswr_column = find_phase.index('VSWR [(VSWR)]')
            phase_value = 'Phase [\xb0]'
            try:
                phase_column = find_phase.index(phase_value)
            except ValueError:
                phase_value = 'Phase [\xef\xbf\xbd]'
                phase_column = find_phase.index(phase_value)
            it = 0
            while (abs(vswr_column - freq_column) > 2) or (abs(phase_column - freq_column) > 2):
                # data is from different sweeps (not the first sweep)
                find_phase.remove('')
                find_phase.remove(find_phase[2])
                find_phase.remove(find_phase[1])
                find_phase.remove(find_phase[0])
                # print find_phase
                it = it + 1
                freq_column = find_phase.index('Freq. [Hz]') + 4 * it
                vswr_column = find_phase.index('VSWR [(VSWR)]') + 4 * it
                phase_column = find_phase.index(phase_value) + 4 * it
            # print freq_column, vswr_column, phase_column
            main_data[i] = np.zeros((len(lines) - 46,),
                                    dtype=[('freq', 'i4'), ('receive_power', 'f4'),
                                           ('phase', 'f4')])
            for ln in range(lines.index(header_line) + 1, lines.index(header_line) +
                    number_of_data_points + 1):
                data = lines[ln].split(",", 16)
                # only taking the same sweep data (3 columns in a row)
                VSWR = float(data[vswr_column])
                # reflection_coeff=abs((VSWR-1)/(VSWR+1))
                # z_balun_junction=50*abs((1+reflection_coeff)/(1-reflection_coeff)) # 50 ohm cable is Z-naught.
                # print VSWR

                return_loss = 20 * math.log(((VSWR + 1) / (VSWR - 1)),
                                            10)  # this is dB measured at instrument.
                # calculate mismatch error. need to adjust power base to power at antenna mismatch.
                power_outgoing = 10 ** (-cable_loss / 10)  # ratio to 1, approaching the balun point.
                # taking into account reflections for mismatch at antenna = S11
                # get single-direction data by making the power base = power_outgoing (incident at mismatch point at balun).

                reflected_loss = -return_loss + cable_loss  # dB, at mismatch point that is reflected.

                returned_power = 10 ** (reflected_loss / 10)
                if returned_power > power_outgoing:
                    print "Antenna: {}".format(i)
                    print data[freq_column]
                    print "wRONG"
                    print returned_power, reflected_loss
                    print power_outgoing, cable_loss
                try:
                    reflection = 10 * math.log((returned_power / power_outgoing), 10)
                    transmission = 10 * math.log((1 - (returned_power / power_outgoing)), 10)
                except ValueError:
                    reflection = 0
                    transmission = -10000
                # this is single direction reflection at mismatch point, assume this happens on
                # incoming receives as well at this point (reflection coefficient is same in both directions)
                # what is the transmitted power through that point then (which is relative the signal incident upon it)?

                receive_power = transmission - cable_loss  # power incoming from antenna will have mismatch point and then cable losses.
                # print "Received Power from Incident at Antenna: {}".format(receive_power)
                receive_power = round(receive_power, 5)
                main_data[i][ln - 46] = (
                data[freq_column], receive_power, float(data[phase_column]) / 2)

    for i in vswr_intf_files.keys():
        with open(data_location + vswr_intf_files[i], 'r') as csvfile:
            lines = csvfile.readlines()
            for ln in lines:
                if ln.find('Freq. [Hz]') != -1:  # found the right line
                    header_line = ln
                    break
            find_phase = header_line.split(",", 16)
            print i
            # print find_phase
            freq_column = find_phase.index('Freq. [Hz]')
            vswr_column = find_phase.index('VSWR [(VSWR)]')
            phase_value = 'Phase [\xb0]'
            try:
                phase_column = find_phase.index(phase_value)
            except ValueError:
                phase_value = 'Phase [\xef\xbf\xbd]'
                phase_column = find_phase.index(phase_value)
            it = 0
            while (abs(vswr_column - freq_column) > 2) or (abs(phase_column - freq_column) > 2):
                # data is from different sweeps (not the first sweep)
                find_phase.remove('')
                find_phase.remove(find_phase[2])
                find_phase.remove(find_phase[1])
                find_phase.remove(find_phase[0])
                # print find_phase
                it = it + 1
                freq_column = find_phase.index('Freq. [Hz]') + 4 * it
                vswr_column = find_phase.index('VSWR [(VSWR)]') + 4 * it
                phase_column = find_phase.index(phase_value) + 4 * it
            # print freq_column, vswr_column, phase_column
            intf_data[i] = np.zeros((len(lines) - 46,),
                                    dtype=[('freq', 'i4'), ('receive_power', 'f4'),
                                           ('phase', 'f4')])
            for ln in range(lines.index(header_line) + 1, lines.index(header_line) + number_of_data_points + 1):
                data = lines[ln].split(",", 16)
                # if ln==lines.index(header_line)+1:
                #    print data
                # only taking first sweep data (columns 1-3)
                # print data[vswr_column]
                VSWR = float(data[vswr_column])
                return_loss = 20 * math.log(((VSWR + 1) / (VSWR - 1)), 10)
                # calculate mismatch error. need to adjust power base to power at antenna mismatch.
                power_outgoing = 10 ** (-cable_loss / 10)  # ratio to 1.
                # taking into account reflections for mismatch at antenna = S11
                # get single-direction data by making the power base = power_outgoing (incident at mismatch point at balun).

                reflected_loss = -return_loss + cable_loss  # dB, at mismatch point.
                returned_power = 10 ** (reflected_loss / 10)
                reflection = 10 * math.log((returned_power / power_outgoing), 10)
                # this is single direction reflection at mismatch point, assume this happens on incoming receives as well at this point (reflection coefficient is same in both directions)
                # what is the transmitted power through that point then, relative to signal incident upon it?
                transmission = 10 * math.log((1 - (returned_power / power_outgoing)), 10)

                receive_power = transmission - cable_loss  # power incoming from antenna will have mismatch point and then cable losses.
                receive_power = round(receive_power, 5)
                # receive_power=-return_loss
                # convert S11 phase offset into a single direction (/2)
                intf_data[i][ln - 46] = (
                data[freq_column], receive_power, float(data[phase_column]) / 2)
                # time.sleep(1)
                # print main_data[i][ln-46]['freq']

    # now we have data points at same frequencies.
    # next - sum signals.
    combined_main_array = np.zeros((number_of_data_points,), dtype=[('freq', 'i4'), ('receive_power', 'f4'), ('phase', 'f4')])
    for i in range(0, number_of_data_points):
        combined_main_array[i]['phase'] = main_data[1][i]['phase']
        combined_main_array[i]['freq'] = main_data[1][i]['freq']
        combined_main_array[i]['receive_power'] = main_data[1][i]['receive_power']

    for ant in main_data.keys():
        print ant
        if ant == 1:
            continue  # skip, do not add
        for i in range(0, number_of_data_points):
            if combined_main_array[i]['freq'] != main_data[ant][i]['freq']:
                errmsg = "Frequencies not Equal"
                sys.exit(errmsg)
            phase_rads1 = -((2 * math.pi * combined_main_array[i]['phase'] / 360) % (
            2 * math.pi))  # convert to rads - negative because we are using proof using cos(x-A)
            phase_rads2 = -((2 * math.pi * main_data[ant][i]['phase'] / 360) % (2 * math.pi))
            amplitude_1 = 10 ** (
            combined_main_array[i]['receive_power'] / 20)  # we want voltage amplitude so use /20
            amplitude_2 = 10 ** (main_data[ant][i]['receive_power'] / 20)
            # print amplitude_2
            combined_amp_squared = (
            amplitude_1 ** 2 + amplitude_2 ** 2 + 2 * amplitude_1 * amplitude_2 * math.cos(
                phase_rads1 - phase_rads2))
            combined_amp = math.sqrt(combined_amp_squared)
            combined_main_array[i]['receive_power'] = 20 * math.log(combined_amp,
                                                           10)  # we based it on amplitude of 1 at each antenna.
            combined_phase = math.atan2(
                amplitude_1 * math.sin(phase_rads1) + amplitude_2 * math.sin(phase_rads2),
                amplitude_1 * math.cos(phase_rads1) + amplitude_2 * math.cos(phase_rads2))
            combined_main_array[i]['phase'] = -combined_phase * 360 / (
            2 * math.pi)  # this is negative so make it positive cos(x-theta)
            # print combined_amp
            # print combined_main_array[3]['receive_power']

    # do the same for the interferometer array.
    combined_intf_array = np.zeros((number_of_data_points,), dtype=[('freq', 'i4'), ('receive_power', 'f4'), ('phase', 'f4')])
    for i in range(0, number_of_data_points):
        combined_intf_array[i]['phase'] = intf_data[1][i]['phase']
        combined_intf_array[i]['freq'] = intf_data[1][i]['freq']
        combined_intf_array[i]['receive_power'] = intf_data[1][i]['receive_power']

    for ant in intf_data.keys():
        if ant == 1:
            continue  # skip, do not add
        for i in range(0, number_of_data_points):
            if combined_intf_array[i]['freq'] != intf_data[ant][i]['freq']:
                errmsg = "Frequencies not Equal"
                sys.exit(errmsg)
            phase_rads1 = -((2 * math.pi * combined_intf_array[i]['phase'] / 360) % (
            2 * math.pi))  # will be in rads already.
            phase_rads2 = -((2 * math.pi * intf_data[ant][i]['phase'] / 360) % (2 * math.pi))
            amplitude_1 = 10 ** (combined_intf_array[i]['receive_power'] / 20)
            amplitude_2 = 10 ** (intf_data[ant][i]['receive_power'] / 20)
            combined_amp = math.sqrt(
                amplitude_1 ** 2 + amplitude_2 ** 2 + 2 * amplitude_1 * amplitude_2 * math.cos(
                    phase_rads1 - phase_rads2))
            combined_intf_array[i]['receive_power'] = 20 * math.log(combined_amp,
                                                           10)  # we based it on amplitude of 1 at each antenna.
            combined_phase = math.atan2(
                amplitude_1 * math.sin(phase_rads1) + amplitude_2 * math.sin(phase_rads2),
                amplitude_1 * math.cos(phase_rads1) + amplitude_2 * math.cos(phase_rads2))
            combined_intf_array[i]['phase'] = -combined_phase * 360 / (2 * math.pi)

    # now compute difference between the arrays in phase due to antennas/feedlines disparity.
    array_diff = np.zeros((number_of_data_points,), dtype=[('freq', 'i4'), ('receive_power', 'f4'), ('phase', 'f4')])
    for i in range(0, number_of_data_points):
        array_diff[i]['freq'] = combined_intf_array[i]['freq']
        array_diff[i]['phase'] = ((combined_main_array[i]['phase'] - combined_intf_array[i]['phase']) % 360)
        if array_diff[i]['phase'] > 180:
            array_diff[i]['phase'] = -360 + array_diff[i]['phase']

    # plot the two arrays on the same plot and then plot the difference in phase between the arrays.
    fig, smpplot = plt.subplots(3, sharex=True)
    xmin, xmax, ymin, ymax = smpplot[0].axis(xmin=8e6, xmax=20e6)
    smpplot[0].set_title(S12_arrays_plot_title)
    smpplot[0].plot(combined_main_array['freq'], combined_main_array['phase'])
    smpplot[1].plot(combined_main_array['freq'], combined_main_array['receive_power'])
    smpplot[0].plot(combined_intf_array['freq'], combined_intf_array['phase'])
    smpplot[1].plot(combined_intf_array['freq'], combined_intf_array['receive_power'])
    smpplot[2].set_xlabel('Frequency (Hz)')
    smpplot[0].set_ylabel('S12 Phase of\nArrays [degrees]')  # from antenna to feedline end at building.
    smpplot[1].set_ylabel('Combined\nArray [dB]')  # referenced to power at a single antenna
    smpplot[0].grid()
    smpplot[1].grid()
    print "plotting"
    smpplot[2].plot(array_diff['freq'], array_diff['phase'])
    smpplot[2].grid()
    # smpplot[2].set_title(diff_S12_plot_title)
    smpplot[2].set_ylabel('S12 Phase\nDifference Between\nArrays [degrees]')
    fig.savefig(plot_location + 'antenna-feedlines-difference.png')
    plt.close(fig)


main()
