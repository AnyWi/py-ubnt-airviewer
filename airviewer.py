#
# Copyright (c) 2016, AnyWi Technologies BV
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# 
# UBNT airView alternative mockup for the Java client, with added functionality
# of storing data for later analytics
#
# Rick van der Zwet <rick.vanderzwet@anywi.com>
#
import requests
import telnetlib
import time
import sys

import numpy as np
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as plticker

USERNAME = 'ubnt'
PASSWORD = 'ubnt'
HOST = "192.168.1.20"
PORT = 18888
TIMEOUT = 10

def usage():
    print "Usage:" + sys.argv[0] + " <live|replay FILENAME>"
    print ""
    print "Options:"
    print "\tlive              \t=\tProcess live data from device " + HOST
    print "\treplay FILENAME   \t=\tReplay FILENAME"
    exit(128)

if len(sys.argv) == 2 and sys.argv[1] == 'live':
    FILENAME = None
elif len(sys.argv) == 3 and sys.argv[1] == 'replay':
    FILENAME = sys.argv[2] # Stored data processing
else:
    usage()



def parse_get_frame_resp(line):
    _,vals_raw = line.split(':')
    vals = map(int, vals_raw.split(','))
    frame_nr = vals.pop(0)
    return(frame_nr, vals)

#TODO: Make me dynamic parse from 'SCAN RANGE' response
scan_range_begin = 2402000000
scan_range_end = 2497000000

if not FILENAME:
    print "Enabling Ubiquiti airView at %s:%s@%s..." %(USERNAME, PASSWORD, HOST)
    s = requests.session()
    s.get('http://' + HOST + '/login.cgi')
    s.post('http://' + HOST + '/login.cgi', 
        {"username": USERNAME, "password": PASSWORD, "uri": "airview.cgi?start=1"})
    
    
    print "Waiting for device to enter airView modus..."
    # Allow device a few moments to settle
    time.sleep(TIMEOUT)
    
    print "Start scanning..."
    tn = telnetlib.Telnet(HOST, PORT, timeout=TIMEOUT)
    #tn.set_debuglevel(99)
    
    # Storage on unique files
    outfile = 'output-%s.dat' % int(time.time())
    print "Storing output at '%s'" % outfile
    fh = open(outfile, 'a')
    def writeline(cmd):
        """ Write line to device"""
        ts = time.time()
        tn.write(cmd)
        print cmd 
        fh.write("%s\001%s" % (ts, cmd))
        return ts
        
    
    def getline():
        """Read line from device"""
        line = tn.read_until("\n")
        print line
        fh.write("%s\001%s" % (time.time(), line))
        return line
    
    # Commands needs to have a trailing space if no arguments specified
    writeline("CONNECT: \n")
    getline()
    
    #writeline("REQUEST RANGE: 2402000000,2407000000\n") #  5 MHz
    #writeline("REQUEST RANGE: 2402000000,2412000000\n") # 10 MHz
    #writeline("REQUEST RANGE: 2402000000,2417000000\n") # 15 MHz
    #writeline("REQUEST RANGE: 2402000000,2422000000\n") # 20 Mhz
    #writeline("REQUEST RANGE: 2402000000,2477000000\n") # (ch 1-11 - US allocation)
    #writeline("REQUEST RANGE: 2402000000,2487000000\n") # (ch 1-13 - UK allocation)
    writeline("REQUEST RANGE: 2402000000,2497000000\n") # (ch 1-14)
    getline()
    
    writeline("START SCAN: \n")
    getline()
    print "Waiting for scan to start..."
    time.sleep(2)

    def get_frame(frame):
        """ Get frame from device airView """
        # TODO: Receiving frames in order, sometimes yield of empty responses. Already flush out maybe?
        #writeline("GET FRAME: %s\n" % frame)
        ts = writeline("GET FRAME: \n")
        line = getline()
        return((ts,) + parse_get_frame_resp(line))
else:
    # No need for logic since we are processing stored data
    sh = open(FILENAME, 'r')
    def get_frame(frame):
        """ Perform replay data processing """
        while True:
            line = sh.readline()
            if not line:
                return(None, None, None)
            ts_raw, a = line.split('\001', 1)
            ts = float(ts_raw)
            cmd, ret = a.split(':', 1)
            if cmd == 'FRAME':
                return((ts,) + parse_get_frame_resp(a))
            

# Get innitial frame number and bins sizes
_, frame_nr, vals = get_frame(None)
bin_size = len(vals)
bin_sample_khz = float(scan_range_end - scan_range_begin) / 1000 / bin_size
print "Bin size: %s" % bin_size


# Start making picture
fig, ax = plt.subplots(figsize=(10,11))
fig.canvas.set_window_title('UBNT airView Client')
ax.set_ylabel('100ms units elapsed')
ax.set_xlabel('Frequency (sampled with bins of %s kHz)' % bin_sample_khz)

# Channel center frequencies
a = [2402,2412,2417,2422,2427,2432,2437,2442,2447,2452,2457,2462,2467,2472,2484,2497]
channels = (np.array(a,dtype='float32') - 2402) / (bin_sample_khz / 1000)
ax.get_xaxis().set_ticks(channels)
plt.xticks(rotation=90)

# Plot channel description
for i in range(1,15):
    width_20mhz = 20000.0 / bin_sample_khz
    if i in [1,6,11,14]:
        pac = mpatches.Arc([channels[i], 0], width_20mhz, 100, 
            theta2=180, linestyle='solid', linewidth=2, color='black')
    else:
        pac = mpatches.Arc([channels[i], 0], width_20mhz, 100, 
            theta2=180, linestyle='dashed', linewidth=2, color='black')
    ax.add_patch(pac)


ax.get_xaxis().set_major_formatter(
    plticker.FuncFormatter(lambda x, p: format(int((x * bin_sample_khz / 1000) + 2402), ',')))

plt.grid(linewidth=2,linestyle='solid',color='black')
plt.tight_layout()

# Initial data and history of 500 samples
matrix = np.empty([500,bin_size]) * np.nan
pcm = ax.pcolorfast(matrix, vmin=-122, vmax=-30)


#
# Matplotlib Animation
#
def update(data):
    global frame_nr
    frame_nr += 1
    ts, frame_nr, row = get_frame(frame_nr)
    # We are on the end of the file
    if not ts and not frame_nr and not row:
        return
    #row = np.random.randint(255, size=(1,100))
    matrix = np.vstack([row, pcm.get_array()[:-1]])
    pcm.set_array(matrix)
    ax.set_title('Frame %s at %s' % (frame_nr, time.asctime(time.localtime(ts))))
    
ani = animation.FuncAnimation(fig, update, interval=100)
plt.show()
        
        
#
# Takes some time (10 seconds) for device to return to an active state
#
