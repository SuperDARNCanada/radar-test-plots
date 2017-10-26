#!/usr/bin/python

# total_path_phase_diff.py
# To measure the total phase difference from antenna to
# Output of phasing matrix in order to compare the main
# and interferometer arrays. This will allow us to the see
# the frequency dependence, find the linear best fit and
# use this to determine a tdiff. This script uses multiple measurements -
#   1. VSWR from feedline out to antenna
#   2. transmitter receive paths and cable paths for interferometer paths
#   3. phasing matrix path - including any cable from the transmitter
# We will use phase and magnitude data.

import sys
import time
import math
import numpy as np
import matplotlib.pyplot as plt

#VSWR and S11 phasing of antennas/feedlines.
S11directory='./S11/'
S11main_files={1:'0129.csv',2:'0128.csv',3:'0127.csv',4:'0126.csv',5:'0125.csv',6:'0124.csv',7:'0123.csv',8:'0121.csv',9:'0131.csv',10:'0132.csv',11:'0134.csv',12:'0136.csv',13:'0137.csv',14:'0138.csv',15:'0139.csv',16:'0130.csv'}
main_data={}
S11intf_files={1:'0145.csv',2:'0146.csv',3:'0147.csv',4:'0148.csv'}
intf_data={}

# transmitter receive paths
TX=False
TXdirectory='./TX/'
TX_files={1:'0152.csv',2:'0154.csv',3:'0153.csv',4:'0155.csv',5:'0156.csv',6:'0157.csv',7:'0158.csv',8:'0159.csv',9:'0160.csv',10:'0161.csv',11:'0162.csv',12:'0163.csv',13:'0164.csv',14:'0165.csv',15:'0166.csv',16:'0167.csv'}

#individual receiver phasing matrix throughput. NOTE THAT this was calibrated to RX1 so we have to assume all zeroes for RX1 data.
#copied data into 0000.csv and replaced data with all zeroes for this.
PM=True
PMdirectory='./PM/AFTER/'
PMmain_files={1:'0000.csv',2:'0207.csv',3:'0208.csv',4:'0209.csv',5:'0210.csv',6:'0211.csv',7:'0212.csv',8:'0213.csv',9:'0214.csv',10:'0216.csv',11:'0217.csv',12:'0218.csv',13:'0219.csv',14:'0220.csv',15:'0221.csv',16:'0222.csv'}
PMintf_files={1:'0227.csv',2:'0229.csv',3:'0230.csv',4:'0231.csv'}

# SET PLOT TITLES AND FILE NAMES:
combined_plot_title1='Inuvik Combined Main and IF Arrays \nAntenna/Feedlines June 2015'
diff_plot_title1='Inuvik Phase Differences between \nArrays Antenna/Feedlines June 2015'
combined_plot_name1='./S11/combined_from_antennasinv.png'
diff_plot_name1='./S11/array_phase_diffinv.png'
combined_plot_title2='Inuvik Combined Main and IF Arrays \nto PM Output June 2015'
diff_plot_title2='Inuvik Phase Differences between \nArrays to PM Output June 2015'
combined_plot_name2='./PM/AFTER/combined_from_antennasinv.png'
diff_plot_name2='./PM/AFTER/array_phase_diffinv.png'

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
    for i in S11main_files.keys():
        with open(S11directory+S11main_files[i],'r') as csvfile:
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
                main_data[i][ln-lines.index(header_line)-1]=(data[freq_column],receive_power,float(data[phase_column])/2)


    # test plot for phase
    #fig1, testplot=plt.subplots(1,1)
    #testplot.plot(main_data[4]['freq'],main_data[4]['phase'])
    #fig1.savefig('./testplot.png')
    #plt.close()

    for i in S11intf_files.keys():
        with open(S11directory+S11intf_files[i],'r') as csvfile:
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
                intf_data[i][ln-lines.index(header_line)-1]=(data[freq_column],receive_power,float(data[phase_column])/2)
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
            phase_rads1=-((2*math.pi*intf_array[i]['phase']/360)%(2*math.pi)) 
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
    smpplot[0].set_title(combined_plot_title1)
    smpplot[0].plot(main_array['freq'],main_array['phase'])
    smpplot[1].plot(main_array['freq'],main_array['receive_power'])
    smpplot[0].plot(intf_array['freq'],intf_array['phase'])
    smpplot[1].plot(intf_array['freq'],intf_array['receive_power'])
    smpplot[1].set_xlabel('Frequency (Hz)')
    smpplot[0].set_ylabel('Phase of S12, degrees') #from antenna to feedline end at building.
    smpplot[1].set_ylabel('Combined Array dB') # referenced to power at a single antenna
    fig.savefig(combined_plot_name1)
    plt.close(fig)
    print "plotting"

    fig, smpplot=plt.subplots(1,1)
    xmin, xmax, ymin, ymax=smpplot.axis(xmin=8e6,xmax=20e6)
    smpplot.plot(array_diff['freq'],array_diff['phase'])
    smpplot.set_title(diff_plot_title1)
    smpplot.set_xlabel('Frequency [Hz]')
    smpplot.set_ylabel('Phase Difference Between Arrays [degrees]')
    fig.savefig(diff_plot_name1)
    plt.close(fig)

    # WE HAVE PLOTTED for S11 DATA ONLY
    # NOW LET'S CONSIDER EFFECTS OF TRANSMITTER PATH AND PHASING MATRIX

    # NOTE: For INV we have phase offset data for interferometer from feedline to phasing matrix 
    # included in the PM data 

    # TX receive paths
    if TX==True:
        for i in TX_files.keys():
            with open(TXdirectory+TX_files[i],'r') as TXfile:
            # we have main_data[i] as numpy array of freq, receive power, and phase from antenna to feedline end (really its S12).
                lines=TXfile.readlines()
                for ln in lines:
                    if ln.find('Freq. [Hz]')!=-1: #found the right line
                        header_line=ln
                        break
                find_phase=header_line.split(",",16)
                #print find_phase
                freq_column=find_phase.index('Freq. [Hz]')
                mag_column=find_phase.index('Magnitude [dB]')
                phase_value='Phase [\xb0]'
                try:
                    phase_column=find_phase.index(phase_value)
                except ValueError:
                    phase_value='Phase [\xef\xbf\xbd]'
                    phase_column=find_phase.index(phase_value)
                it=0
                while (abs(mag_column-freq_column)>2) or (abs(phase_column-freq_column)>2):
                    #data is from different sweeps (not the first sweep)
                    find_phase.remove('')
                    find_phase.remove(find_phase[2])
                    find_phase.remove(find_phase[1])
                    find_phase.remove(find_phase[0])
                    #print find_phase
                    it=it+1
                    freq_column=find_phase.index('Freq. [Hz]')+4*it
                    mag_column=find_phase.index('Magnitude [dB]')+4*it
                    phase_column=find_phase.index(phase_value)+4*it
                if len(lines)==(lines.index(header_line)+402):
                    for j in range(222,22,-1):
                        lines.remove(lines[2*j+1])
                for ln in range(lines.index(header_line)+1,lines.index(header_line)+202):
                    data=lines[ln].split(",",16)
                    #only taking the same sweep data (3 columns in a row)
                    mag=float(data[mag_column])
                    ph=float(data[phase_column])
                    # add this magnitude (dB loss) to the magnitude of the incoming signal in main_data[i].
                    if main_data[i][ln-lines.index(header_line)-1]['freq']!=float(data[freq_column]):
                        print "Error:frequencies not equal" #so you should not add this phase offset and loss
                        sys.exit()
                    main_data[i][ln-lines.index(header_line)-1]['receive_power']=main_data[i][ln-lines.index(header_line)-1]['receive_power']+mag
                    main_data[i][ln-lines.index(header_line)-1]['phase']=main_data[i][ln-lines.index(header_line)-1]['phase']+ph
                

    # Phasing matrix data, for Inuvik this includes the cable from interferometer feedlines to the phasing matrix.
    # Do the same thing, add the phase offset and loss to the data in the main_data and intf_data

    if PM==True:
        for i in PMmain_files.keys():
            with open(PMdirectory+PMmain_files[i],'r') as PMfile:
            # we have main_data[i] as numpy array of freq, receive power, and phase from antenna to feedline end (really its S12).
                lines=PMfile.readlines()
                for ln in lines:
                    if ln.find('Freq. [Hz]')!=-1: #found the right line
                        header_line=ln
                        break
                find_phase=header_line.split(",",16)
                #print find_phase
                freq_column=find_phase.index('Freq. [Hz]')
                mag_column=find_phase.index('Magnitude [dB]')
                phase_value='Phase [\xb0]'
                try:
                    phase_column=find_phase.index(phase_value)
                except ValueError:
                    phase_value='Phase [\xef\xbf\xbd]'
                    phase_column=find_phase.index(phase_value)
                it=0
                while (abs(mag_column-freq_column)>2) or (abs(phase_column-freq_column)>2):
                    #data is from different sweeps (not the first sweep)
                    find_phase.remove('')
                    find_phase.remove(find_phase[2])
                    find_phase.remove(find_phase[1])
                    find_phase.remove(find_phase[0])
                    #print find_phase
                    it=it+1
                    freq_column=find_phase.index('Freq. [Hz]')+4*it
                    mag_column=find_phase.index('Magnitude [dB]')+4*it
                    phase_column=find_phase.index(phase_value)+4*it
                if len(lines)==(lines.index(header_line)+402):
                    for j in range(222,22,-1):
                        lines.remove(lines[2*j+1])
                for ln in range(lines.index(header_line)+1,lines.index(header_line)+202):
                    data=lines[ln].split(",",16)
                    #only taking the same sweep data (3 columns in a row)
                    mag=float(data[mag_column])
                    ph=float(data[phase_column])
                    # add this magnitude (dB loss) to the magnitude of the incoming signal in main_data[i].
                    if main_data[i][ln-lines.index(header_line)-1]['freq']!=float(data[freq_column]):
                        print "Error:frequencies not equal" #so you should not add this phase offset and loss
                        sys.exit()
                    main_data[i][ln-lines.index(header_line)-1]['receive_power']=main_data[i][ln-lines.index(header_line)-1]['receive_power']+mag
                    main_data[i][ln-lines.index(header_line)-1]['phase']=main_data[i][ln-lines.index(header_line)-1]['phase']+ph
        
        for i in PMintf_files.keys():
            with open(PMdirectory+PMintf_files[i],'r') as PMfile:
            # we have main_data[i] as numpy array of freq, receive power, and phase from antenna to feedline end (really its S12).
                lines=PMfile.readlines()
                for ln in lines:
                    if ln.find('Freq. [Hz]')!=-1: #found the right line
                        header_line=ln
                        break
                find_phase=header_line.split(",",16)
                #print find_phase
                freq_column=find_phase.index('Freq. [Hz]')
                mag_column=find_phase.index('Magnitude [dB]')
                phase_value='Phase [\xb0]'
                try:
                    phase_column=find_phase.index(phase_value)
                except ValueError:
                    phase_value='Phase [\xef\xbf\xbd]'
                    phase_column=find_phase.index(phase_value)
                it=0
                while (abs(mag_column-freq_column)>2) or (abs(phase_column-freq_column)>2):
                    #data is from different sweeps (not the first sweep)
                    find_phase.remove('')
                    find_phase.remove(find_phase[2])
                    find_phase.remove(find_phase[1])
                    find_phase.remove(find_phase[0])
                    #print find_phase
                    it=it+1
                    freq_column=find_phase.index('Freq. [Hz]')+4*it
                    mag_column=find_phase.index('Magnitude [dB]')+4*it
                    phase_column=find_phase.index(phase_value)+4*it
                if len(lines)==(lines.index(header_line)+402):
                    for j in range(222,22,-1):
                        lines.remove(lines[2*j+1])
                for ln in range(lines.index(header_line)+1,lines.index(header_line)+202):
                    data=lines[ln].split(",",16)
                    #only taking the same sweep data (3 columns in a row)
                    mag=float(data[mag_column])
                    ph=float(data[phase_column])
                    # add this magnitude (dB loss) to the magnitude of the incoming signal in main_data[i].
                    if main_data[i][ln-lines.index(header_line)-1]['freq']!=float(data[freq_column]):
                        print "Error:frequencies not equal" #so you should not add this phase offset and loss
                        sys.exit()
                    intf_data[i][ln-lines.index(header_line)-1]['receive_power']=intf_data[i][ln-lines.index(header_line)-1]['receive_power']+mag
                    intf_data[i][ln-lines.index(header_line)-1]['phase']=intf_data[i][ln-lines.index(header_line)-1]['phase']+ph

    if PM==True or TX==True:
        # REPLOT the DATA with this factored in.
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
                phase_rads1=-((2*math.pi*intf_array[i]['phase']/360)%(2*math.pi)) 
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
        smpplot[0].set_title(combined_plot_title2)
        smpplot[0].plot(main_array['freq'],main_array['phase'])
        smpplot[1].plot(main_array['freq'],main_array['receive_power'])
        smpplot[0].plot(intf_array['freq'],intf_array['phase'])
        smpplot[1].plot(intf_array['freq'],intf_array['receive_power'])
        smpplot[1].set_xlabel('Frequency (Hz)')
        smpplot[0].set_ylabel('Phase of S12, degrees') #from antenna to output of phasing matrix.
        smpplot[1].set_ylabel('Combined Array dB') # referenced to power at a single antenna
        fig.savefig(combined_plot_name2)
        plt.close(fig)
        print "plotting"

        fig, smpplot=plt.subplots(1,1)
        xmin, xmax, ymin, ymax=smpplot.axis(xmin=8e6,xmax=20e6)
        smpplot.plot(array_diff['freq'],array_diff['phase'])
        smpplot.set_title(diff_plot_title2)
        smpplot.set_xlabel('Frequency [Hz]')
        smpplot.set_ylabel('Phase Difference Between Arrays [degrees]')
        fig.savefig(diff_plot_name2)
        plt.close(fig)

main()
