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
import csv

# General variables to change depending on data being used
radar_name = sys.argv[1]
data_location = sys.argv[2]
plot_location = sys.argv[3]
vswr_main_files_str = sys.argv[4]
vswr_intf_files_str = sys.argv[5]

S12_arrays_plot_title = radar_name + ' Combined Main and IF Arrays \nAntenna/Feedlines'
data_description = 'This data was taken on site visits in August 2017.'

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
    main_data = {}
    intf_data = {}
    for k,v in vswr_main_files.iteritems():
        with open(data_location + v, 'r') as csvfile:
            while not 'Freq. [Hz]' in csvfile.readline(): #skip to header
                pass
            next(csvfile) #skip over header
            csv_reader = csv.reader(csvfile)

            data = []
            for row in csv_reader:
                try:
                    freq = float(row[0])
                except:
                    continue
                VSWR = float(row[1])
                phase = float(row[2])

                return_loss = 20 * math.log(((VSWR + 1) / (VSWR - 1)),
                                            10)  # this is dB measured at instrument.
                # calculate mismatch error. need to adjust power base to power at antenna mismatch.
                power_outgoing = 10 ** (-1*cable_loss / 10)  # ratio to 1, approaching the balun point.
                # taking into account reflections for mismatch at antenna = S11
                # get single-direction data by making the power base = power_outgoing (incident at mismatch point at balun).

                reflected_loss = -1*return_loss + cable_loss  # dB, at mismatch point that is reflected.

                returned_power = 10 ** (reflected_loss / 10)
                if returned_power > power_outgoing:
                    print "Antenna: {}".format(k)
                    print freq
                    print "WRONG"
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
                data.append((freq, receive_power, float(phase) / 2))
            data = np.array(data,dtype=[('freq', 'i4'),('receive_power', 'f4'),('phase', 'f4')])
            main_data[k] = data



    for k,v in vswr_intf_files.iteritems():
        with open(data_location + v, 'r') as csvfile:
            while not 'Freq. [Hz]' in csvfile.readline(): #skip to header
                pass
            next(csvfile) #skip over header
            csv_reader = csv.reader(csvfile)

            data = []
            for row in csv_reader:
                try:
                    freq = float(row[0])
                except:
                    continue
                VSWR = float(row[1])
                phase = float(row[2])

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
                # convert S11 phase offset into a single direction (/2)
                data.append((freq, receive_power, float(phase) / 2))

            data = np.array(data,dtype=[('freq', 'i4'),('receive_power', 'f4'),('phase', 'f4')])
            intf_data[k] = data

    def combine_arrays(array_dict):
        for k,v in array_dict.iteritems():
            for a,b in zip(array_dict[1],v):
                if a['freq'] != b['freq']:
                    errmsg = "Frequencies not Equal"
                    sys.exit(errmsg)

        # now we have data points at same frequencies.
        # next - sum signals.
        number_of_data_points = len(array_dict[1])

        combined_array = np.copy(array_dict[1])

        for k,v in array_dict.iteritems():
            print k
            if k == 1:
                continue  # skip, do not add
            for c,a in zip(combined_array,v):
                if c['freq'] != a['freq']:
                    errmsg = "Frequencies not Equal"
                    sys.exit(errmsg)

                # convert to rads - negative because we are using proof using cos(x-A)
                phase_rads1 = -((2 * math.pi * c['phase'] / 360) % (2 * math.pi))
                phase_rads2 = -((2 * math.pi * a['phase'] / 360) % (2 * math.pi))

                # we want voltage amplitude so use /20
                amplitude_1 = 10 ** (c['receive_power'] / 20)
                amplitude_2 = 10 ** (a['receive_power'] / 20)

                combined_amp_squared = (
                amplitude_1 ** 2 + amplitude_2 ** 2 + 2 * amplitude_1 * amplitude_2 * math.cos(
                    phase_rads1 - phase_rads2))
                combined_amp = math.sqrt(combined_amp_squared)

                # we based it on amplitude of 1 at each antenna.
                c['receive_power'] = 20 * math.log(combined_amp,10)
                combined_phase = math.atan2(
                    amplitude_1 * math.sin(phase_rads1) + amplitude_2 * math.sin(phase_rads2),
                    amplitude_1 * math.cos(phase_rads1) + amplitude_2 * math.cos(phase_rads2))

                # this is negative so make it positive cos(x-theta)
                c['phase'] = -combined_phase * 360 / (2 * math.pi)
        return combined_array

    combined_main_array = combine_arrays(main_data)
    combined_intf_array = combine_arrays(intf_data)

    array_diff = []
    for m,i in zip(combined_main_array,combined_intf_array):
        freq = i['freq']
        phase = ((m['phase'] - i['phase']) % 360)
        if phase > 180:
            phase = -360 + phase
        array_diff.append((freq,phase))
    array_diff = np.array(array_diff,dtype=[('freq', 'i4'),('phase', 'f4')])

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
