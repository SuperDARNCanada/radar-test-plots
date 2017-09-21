#!/usr/bin/python

# Phase_diff.py
# To measure the phase offset in cables, antennas
# using S11 phase measurements, can determine S12 phase
# vs frequency.

import sys
import time
import math
import numpy as np
import matplotlib.pyplot as plt

main_files={1:'0463.csv',2:'0464.csv',3:'0465.csv',4:'0466.csv',5:'0467.csv',6:'0468.csv',7:'0469.csv',8:'0470.csv',9:'0471.csv',10:'0472.csv',11:'0506.csv',12:'0474.csv',13:'0475.csv',14:'0476.csv',15:'0477.csv',16:'0478.csv'}
main_data={}
intf_files={1:'0479.csv',2:'0480.csv',3:'0543.csv',4:'0482.csv'}
intf_data={}

# SET PLOT TITLES:
combined_plot_title='Rankin Inlet Combined Main and IF Arrays \nAntenna/Feedlines After Fixes July 2016'
#intf_plot_title='Rankin Inlet Combined Interferometer Array Antenna/Feedlines After Fixes July 2016'
diff_plot_title='Rankin Inlet Phase Differences between \nArrays Antenna/Feedlines After Fixes July 2016'

# if we assume S12 and S21 are the same (safe for feedlines/antennas only)
# We can assume that S21 phase is S11 phase/2
# We can assume that the transmitted power T12 will be equal to (incident power - cable losses on incident)- (S11 (reflected power) + cable losses on reflect)

#estimated cable losses (LMR-400) @ 0.7 db/100ft * 600ft
cable_loss=3.5 # in dB
# receive power will be calculated from transmit power losses.
# transmit S21 = (incident-cable losses)-(S11+cable losses)
# S11=current return loss referenced to incident = 0dB.
# make incident at port 2 = 0 dB = incident-cable losses = -cable_loss =0
# if we make the power at antenna = 1, and S12 = S21
# receive S12 = incident-reflected_loss_at_balun-cable_loss
# we will calculate reflected loss at balun using our measured reflected loss at instrument, remembering that has cable loss included and was going in two directions.

# amplitudes calculated as if all antennas receive the same signal strength at the antenna. Balun mismatch for each individual antenna is estimated here.

def main():
    for i in main_files.keys():
        with open(main_files[i],'r') as csvfile:
            lines=csvfile.readlines()
            for ln in lines:
                if ln.find('Freq. [Hz]')!=-1: #found the right line
                    header_line=ln
                    break
            find_phase=header_line.split(",",16)
            #print find_phase
            freq_column=find_phase.index('Freq. [Hz]')
            vswr_column=find_phase.index('VSWR [(VSWR)]')
            phase_value='Phase [\xb0]'
            try:
                phase_column=find_phase.index(phase_value)
            except ValueError:
                phase_value='Phase [\xef\xbf\xbd]'
                phase_column=find_phase.index(phase_value)
            it=0
            while (abs(vswr_column-freq_column)>2) or (abs(phase_column-freq_column)>2):
                #data is from different sweeps (not the first sweep)
                find_phase.remove('')
                find_phase.remove(find_phase[2])
                find_phase.remove(find_phase[1])
                find_phase.remove(find_phase[0])
                #print find_phase
                it=it+1
                freq_column=find_phase.index('Freq. [Hz]')+4*it
                vswr_column=find_phase.index('VSWR [(VSWR)]')+4*it
                phase_column=find_phase.index(phase_value)+4*it
            #print freq_column, vswr_column, phase_column
            main_data[i]=np.zeros((len(lines)-46,),dtype=[('freq', 'i4'),('receive_power', 'f4'),('phase', 'f4')])
            #make all arrays of same length with same frequency axis
            if len(lines)==(lines.index(header_line)+402):
                for j in range(222,22,-1):
                    lines.remove(lines[2*j+1])
            for ln in range(lines.index(header_line)+1,lines.index(header_line)+202):
                data=lines[ln].split(",",16)
                #only taking the same sweep data (3 columns in a row)
                VSWR=float(data[vswr_column])
                #reflection_coeff=abs((VSWR-1)/(VSWR+1))
                #z_balun_junction=50*abs((1+reflection_coeff)/(1-reflection_coeff)) # 50 ohm cable is Z-naught.
                #print VSWR
                
                return_loss=20*math.log(((VSWR+1)/(VSWR-1)),10) #this is dB measured at instrument.
                # calculate mismatch error. need to adjust power base to power at antenna mismatch.
                power_outgoing=10**(-cable_loss/10) #ratio to 1, approaching the balun point.
                # taking into account reflections for mismatch at antenna = S11
                # get single-direction data by making the power base = power_outgoing (incident at mismatch point at balun).
                
                reflected_loss=-return_loss+cable_loss #dB, at mismatch point that is reflected.
                
                returned_power=10**(reflected_loss/10)
                if returned_power>power_outgoing:
                    print "Antenna: {}".format(i)
                    print data[freq_column]
                    print "wRONG"
                    print returned_power, reflected_loss
                    print power_outgoing, cable_loss
                try:
                    reflection=10*math.log((returned_power/power_outgoing),10)
                    transmission=10*math.log((1-(returned_power/power_outgoing)),10)
                except ValueError:
                    reflection=0
                    transmission=-10000
                # this is single direction reflection at mismatch point, assume this happens on incoming receives as well at this point (reflection coefficient is same in both directions)
                # what is the transmitted power through that point then (which is relative the signal incident upon it)?

                receive_power=transmission-cable_loss #power incoming from antenna will have mismatch point and then cable losses.
                #print "Received Power from Incident at Antenna: {}".format(receive_power)
                receive_power=round(receive_power,5)
                main_data[i][ln-46]=(data[freq_column],receive_power,float(data[phase_column])/2)

    # test plot for phase
    #fig1, testplot=plt.subplots(1,1)
    #testplot.plot(main_data[4]['freq'],main_data[4]['phase'])
    #fig1.savefig('./testplot.png')
    #plt.close()

    for i in intf_files.keys():
        with open(intf_files[i],'r') as csvfile:
            lines=csvfile.readlines()
            for ln in lines:
                if ln.find('Freq. [Hz]')!=-1: #found the right line
                    header_line=ln
                    break
            find_phase=header_line.split(",",16)
            print i
            #print find_phase
            freq_column=find_phase.index('Freq. [Hz]')
            vswr_column=find_phase.index('VSWR [(VSWR)]')
            phase_value='Phase [\xb0]'
            try:
                phase_column=find_phase.index(phase_value)
            except ValueError:
                phase_value='Phase [\xef\xbf\xbd]'
                phase_column=find_phase.index(phase_value)
            it=0
            while (abs(vswr_column-freq_column)>2) or (abs(phase_column-freq_column)>2):
                #data is from different sweeps (not the first sweep)
                find_phase.remove('')
                find_phase.remove(find_phase[2])
                find_phase.remove(find_phase[1])
                find_phase.remove(find_phase[0])
                #print find_phase
                it=it+1
                freq_column=find_phase.index('Freq. [Hz]')+4*it
                vswr_column=find_phase.index('VSWR [(VSWR)]')+4*it
                phase_column=find_phase.index(phase_value)+4*it
            #print freq_column, vswr_column, phase_column
            intf_data[i]=np.zeros((len(lines)-46,),dtype=[('freq', 'i4'),('receive_power', 'f4'),('phase', 'f4')])
            if len(lines)==(lines.index(header_line)+402):
                for j in range(222,22,-1):
                    lines.remove(lines[2*j+1])
            for ln in range(lines.index(header_line)+1,lines.index(header_line)+202):
                data=lines[ln].split(",",16)
                #if ln==lines.index(header_line)+1:
                #    print data
                #only taking first sweep data (columns 1-3)
                #print data[vswr_column]
                VSWR=float(data[vswr_column])
                return_loss=20*math.log(((VSWR+1)/(VSWR-1)),10)
                # calculate mismatch error. need to adjust power base to power at antenna mismatch.
                power_outgoing=10**(-cable_loss/10) #ratio to 1.
                # taking into account reflections for mismatch at antenna = S11
                # get single-direction data by making the power base = power_outgoing (incident at mismatch point at balun).
                
                reflected_loss=-return_loss+cable_loss #dB, at mismatch point.
                returned_power=10**(reflected_loss/10)
                reflection=10*math.log((returned_power/power_outgoing),10)
                # this is single direction reflection at mismatch point, assume this happens on incoming receives as well at this point (reflection coefficient is same in both directions)
                # what is the transmitted power through that point then, relative to signal incident upon it?
                transmission=10*math.log((1-(returned_power/power_outgoing)),10)

                receive_power=transmission-cable_loss #power incoming from antenna will have mismatch point and then cable losses.
                receive_power=round(receive_power,5)
                #receive_power=-return_loss
                #convert S11 phase offset into a single direction (/2)
                intf_data[i][ln-46]=(data[freq_column],receive_power,float(data[phase_column])/2)
                #time.sleep(1)
                #print main_data[i][ln-46]['freq'] 

    # now we have 200 data points at same frequencies.
    # next - sum signals.
    main_array=np.zeros((201,),dtype=[('freq', 'i4'),('receive_power', 'f4'),('phase', 'f4')])
    for i in range(0,201):
        main_array[i]['phase']=main_data[1][i]['phase']
        main_array[i]['freq']=main_data[1][i]['freq']
        main_array[i]['receive_power']=main_data[1][i]['receive_power']

    for ant in main_data.keys():
        print ant
        if ant==1:
            continue #skip, do not add
        for i in range(0,201):
            if main_array[i]['freq']!=main_data[ant][i]['freq']:
                errmsg="Frequencies not Equal"
                sys.exit(errmsg)
            phase_rads1=-((2*math.pi*main_array[i]['phase']/360)%(2*math.pi)) #convert to rads - negative because we are using proof using cos(x-A)
            phase_rads2=-((2*math.pi*main_data[ant][i]['phase']/360)%(2*math.pi)) 
            amplitude_1=10**(main_array[i]['receive_power']/20) # we want voltage amplitude so use /20
            amplitude_2=10**(main_data[ant][i]['receive_power']/20)
            #print amplitude_2
            combined_amp_squared=(amplitude_1**2+amplitude_2**2+2*amplitude_1*amplitude_2*math.cos(phase_rads1-phase_rads2))
            combined_amp=math.sqrt(combined_amp_squared)
            main_array[i]['receive_power']=20*math.log(combined_amp,10) #we based it on amplitude of 1 at each antenna.
            combined_phase=math.atan2(amplitude_1*math.sin(phase_rads1)+amplitude_2*math.sin(phase_rads2),amplitude_1*math.cos(phase_rads1)+amplitude_2*math.cos(phase_rads2))
            main_array[i]['phase']=-combined_phase*360/(2*math.pi) # this is negative so make it positive cos(x-theta)
        #print combined_amp
        #print main_array[3]['receive_power']

    # do the same for the interferometer array.
    intf_array=np.zeros((201,),dtype=[('freq', 'i4'),('receive_power', 'f4'),('phase', 'f4')])
    for i in range(0,201):
        intf_array[i]['phase']=intf_data[1][i]['phase']
        intf_array[i]['freq']=intf_data[1][i]['freq']
        intf_array[i]['receive_power']=intf_data[1][i]['receive_power']

    for ant in intf_data.keys():
        if ant==1:
            continue #skip, do not add
        for i in range(0,201):
            if intf_array[i]['freq']!=intf_data[ant][i]['freq']:
                errmsg="Frequencies not Equal"
                sys.exit(errmsg)
            phase_rads1=-((2*math.pi*intf_array[i]['phase']/360)%(2*math.pi)) #will be in rads already.
            phase_rads2=-((2*math.pi*intf_data[ant][i]['phase']/360)%(2*math.pi))
            amplitude_1=10**(intf_array[i]['receive_power']/20)
            amplitude_2=10**(intf_data[ant][i]['receive_power']/20)
            combined_amp=math.sqrt(amplitude_1**2+amplitude_2**2+2*amplitude_1*amplitude_2*math.cos(phase_rads1-phase_rads2))
            intf_array[i]['receive_power']=20*math.log(combined_amp,10) #we based it on amplitude of 1 at each antenna.
            combined_phase=math.atan2(amplitude_1*math.sin(phase_rads1)+amplitude_2*math.sin(phase_rads2),amplitude_1*math.cos(phase_rads1)+amplitude_2*math.cos(phase_rads2))
            intf_array[i]['phase']=-combined_phase*360/(2*math.pi)

    # now compute difference between the arrays in phase due to antennas/feedlines disparity.
    array_diff=np.zeros((201,),dtype=[('freq', 'i4'),('receive_power', 'f4'),('phase', 'f4')])
    for i in range(0,201):
        array_diff[i]['freq']=intf_array[i]['freq']
        array_diff[i]['phase']=((main_array[i]['phase']-intf_array[i]['phase'])%360)
        if array_diff[i]['phase']>180:
            array_diff[i]['phase']=-360+array_diff[i]['phase']


    #plot the two arrays on the same plot and then plot the difference in phase between the arrays.
    fig, smpplot=plt.subplots(2, sharex=True)
    xmin, xmax, ymin, ymax=smpplot[0].axis(xmin=8e6,xmax=20e6)
    smpplot[0].set_title(combined_plot_title)
    smpplot[0].plot(main_array['freq'],main_array['phase'])
    smpplot[1].plot(main_array['freq'],main_array['receive_power'])
    smpplot[0].plot(intf_array['freq'],intf_array['phase'])
    smpplot[1].plot(intf_array['freq'],intf_array['receive_power'])
    smpplot[1].set_xlabel('Frequency (Hz)')
    smpplot[0].set_ylabel('Phase of S12, degrees') #from antenna to feedline end at building.
    smpplot[1].set_ylabel('Combined Array dB') # referenced to power at a single antenna
    fig.savefig('./combined_from_antennas.png')
    plt.close(fig)
    print "plotting"

    fig, smpplot=plt.subplots(1,1)
    xmin, xmax, ymin, ymax=smpplot.axis(xmin=8e6,xmax=20e6)
    smpplot.plot(array_diff['freq'],array_diff['phase'])
    smpplot.set_title(diff_plot_title)
    smpplot.set_xlabel('Frequency [Hz]')
    smpplot.set_ylabel('Phase Difference Between Arrays [degrees]')
    fig.savefig('./array_phase_diff.png')
    plt.close(fig)

main()
