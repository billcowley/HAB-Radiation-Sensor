#!/usr/bin/env python
# basic plotting of radiation sensor counts, SHSSP19, Bill
# USE:   ./radplt  datafile.dat  'plot_title'  
#        eg  ./radplt  datafile.dat radval_9feb19.txt
# This version will handle raw values from the uSD card on the payload eg
# 04:13:10: 10,5
# 04:13:12: 10,5
# OR the values from radn_payload_rx.py   eg
# 04:52:20: 769,38; 1549673215,1521
# 04:52:22: 771,38; 1549673217,1533   ie includes time stamp and altitude 

import sys 
import numpy as np
import matplotlib.pyplot as plt

if len(sys.argv)>1:
    DATFILE = sys.argv[1]
else:
    DATFILE  = "radval.txt"

print('\nPlot radiation values from file '+DATFILE)
try:
    dfile = open(DATFILE, "r")
except:
    print("USAGE ..   python radplt.py  [radval.txt]  [plot title]")
    sys.exit()

if len(sys.argv)>2:
    TITL = sys.argv[2]
else:
    TITL = 'SHSSP19 HAB Radiation Measurements'

#print(sys.argv)

rawarray = []
raw2 = []
extra_data = 0

lcount = 0
for st in dfile:
  try:
    # print(st)
    if st.find(';')>-1:
       p3=st.split(';')
       p1=p3[0].split(':')
       p4=p3[1].split(',')
       raw2.append([int(p4[0]), int(p4[1])])
       extra_data=1
    else:
       p1=st.split(':')
    lcount +=1
    
    p2=p1[3].split(',')
    rawarray.append([int(p1[0]), int(p1[1]), int(p1[2]), int(p2[0]), int(p2[1])])
  except:
    print('comment or bad data line: '+st)

print('number of lines read is '+str(lcount))
darray = np.array(rawarray)
d2array = np.array(raw2)


plt.figure(0)
plt.subplot(3,1,1)
plt.title(TITL)
hrs = (darray[:,0]*3600+darray[:,1]*60+darray[:,2])/3600.0; 
plt.plot(hrs, darray[:,3], 'b.')
plt.ylabel('GM Radn Count')
plt.subplot(3,1,2)
plt.plot(hrs, darray[:,4], 'g.')
plt.ylabel('SS Radn Count')
plt.xlabel('Time after midnight (hours)')
if extra_data==1:
    plt.subplot(3,1,3)
    plt.plot((d2array[:,0]-d2array[0,0])/3600.0, d2array[:,1], 'r.')
    plt.ylabel('Altitude ')
    plt.xlabel('Time (hrs from start)')

print('please close plot window when done')
plt.show()


in1 =0; in2=0;  in3 =0; TLIM = 120
dels =[]; done =0; 

while done==0: 
    secs =0
    while secs<TLIM:
        if in2==len(hrs):
            done=1
            break
        secs =  3600.0*(hrs[in2]-hrs[in1])
        cntgm = darray[in2,3]-darray[in1,3]
        cntss = darray[in2,4]-darray[in1,4]
        if extra_data==1:
            x = d2array[in1,1]
        else:
            x = hrs[in1]
        in2+=1
        
    in1=in2
   
    if secs<1.5*TLIM:
        dels.append([x, cntgm, cntss]);
    else:
        print('reject long interval of '+str(secs))     
    
del2 = np.array(dels)   # array- cols are alt, GM incs, SS incs 

plt.figure(1)

plt.subplot(2,1,1)
if extra_data==1: 
    plt.title('Horus52, 9Feb2019: Radiation versus Altitude')
    plt.xlabel('Altitude (m)')
else:
    plt.title('Horus52, 9Feb2019: Radiation versus Time')
    plt.xlabel('Time (hrs)')
plt.plot(del2[:,0], del2[:,1], '+')
plt.ylabel('GM Count per 2 mins')
plt.subplot(2,1,2)
plt.plot(del2[:,0], del2[:,2], '+')
if extra_data==1:
    plt.xlabel('altitude (m)')
plt.ylabel('SS Count per 2 mins')
plt.show()

    
