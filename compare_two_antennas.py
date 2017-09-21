#!/usr/bin/python

# to compare two signals coming from antenna using VSWR data.

import math
import matplotlib.pyplot as plt

file1='./S11/0145.csv'
file2='./S11/0146.csv'

cable_loss=3.5
#assume same number of points
file1line1=48
file2line1=48
freq1=[]
power1=[]
phase1=[]
freq2=[]
power2=[]
phase2=[]

with open(file1, 'r') as f1:
    lines=f1.readlines()
    for ln in range(file1line1,len(lines)-1):
        data=lines[ln].split(',')
        freq1.append(int(data[8]))
        vswr=float(data[9])
        return_loss=20*math.log(((vswr+1)/(vswr-1)),10)
        power_outgoing=10**(-cable_loss/10)
        reflected_loss=-return_loss+cable_loss # reflected power from mismatch point
        returned_power=10**(reflected_loss/10)
        if returned_power>power_outgoing:
            print "WRONG"
            print returned_power, reflected_loss
            print power_outgoing, cable_loss
        transmission=10*math.log((1-(returned_power/power_outgoing)),10)
        receive_power=transmission-cable_loss
        power1.append(receive_power)
        phase1.append(float(data[10])/2)

with open(file2, 'r') as f2:
    lines=f2.readlines()
    for ln in range(file1line1,len(lines)-1):
        data=lines[ln].split(',')
        freq2.append(int(data[8]))
        vswr=float(data[9])
        return_loss=20*math.log(((vswr+1)/(vswr-1)),10)
        power_outgoing=10**(-cable_loss/10)
        reflected_loss=-return_loss+cable_loss # reflected power from mismatch point
        returned_power=10**(reflected_loss/10)
        if returned_power>power_outgoing:
            print "WRONG"
            print returned_power, reflected_loss
            print power_outgoing, cable_loss

        transmission=10*math.log((1-(returned_power/power_outgoing)),10)
        receive_power=transmission-cable_loss
        power2.append(receive_power)
        phase2.append(float(data[10])/2)
        
#for i in range(len(freq1)):
#    if freq1[i]!=freq2[i]:
#        print "ERROR"

#phase_diff=[]
#for i in range(len(phase1)):
#    phase_diff.append(phase2[i]-phase1[i])
#
#fig, test=plt.subplots(1,1)
#test.plot(freq1,phase_diff)
#fig.savefig('./testcompare.png')
#plt.close()

fig, test=plt.subplots(2, sharex=True)
test[0].plot(freq1,power1)
test[0].plot(freq2,power2)
test[1].plot(freq1,phase1)
test[1].plot(freq2,phase2)
fig.savefig('./testplot.png')
plt.close()
