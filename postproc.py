#!/usr/bin/env python3

# quick post-processor for UQ of DALES runs
# reads DALES output files, extracts interesting
# quantities, averages them over last half of the run.
# Writes output to results.csv

import numpy
import json
from netCDF4 import Dataset
import subprocess
import glob

# https://stackoverflow.com/a/136280/1333273
def tail(f, n):
    proc = subprocess.Popen(['tail', '-n', str(n), f], stdout=subprocess.PIPE)
    lines = proc.stdout.readlines()
    return lines


# select time index range for averaging.
# last 4 h or last half of simulation if total time < 8h
def sel_range(time):
    l = len(gcfrac)
    tlast = time[-1]
    if tlast > 8*3600:
        imin = numpy.searchsorted(time, tlast-4*3600)
    else:
        imin = l//2   # average over last half of run
    return imin, l




d = Dataset("tmser.001.nc", 'r')

time1 = d.variables['time'][:]
gcfrac   = d.variables['cfrac'][:]     # global cloud fraction
lwp_bar = d.variables['lwp_bar'][:]
zb = d.variables['zb'][:]
zi = d.variables['zi'][:]
wq = d.variables['wq'][:]
wtheta = d.variables['wtheta'][:]
we = d.variables['we'][:]

imin, l = sel_range(time1)
print('Averaging from %.1f to %.1f h'%(time1[imin]/3600, time1[-1]/3600))

gcfrac_avg = numpy.mean(gcfrac[imin:l])
lwp_bar_avg = numpy.mean(lwp_bar[imin:l])
zb_avg = numpy.mean(zb[imin:l])
zi_avg = numpy.mean(zi[imin:l])
wq_avg = numpy.mean(wq[imin:l])
wtheta_avg = numpy.mean(wtheta[imin:l])
we_avg = numpy.mean(we[imin:l])

p = Dataset("profiles.001.nc", 'r')
# precipitation flux at lowest level
time2   = p.variables["time"][:]  
prec    = p.variables["precmn"][:,0]  
qr      = p.variables["sv002"][:,:]
ql      = p.variables["ql"][:,:]
u       = p.variables["u"][:,:]
v       = p.variables["v"][:,:]
qt      = p.variables["qt"][:,:]
thl     = p.variables["thl"][:,:]
rhof    = p.variables["rhof"][:,:]
zcfrac  = p.variables["cfrac"][:,:]  # z-dependent cloud fraction
zh      = p.variables["zm"][:]       # half-level heights  # dzf(k) = zh(k+1) - zh(k)
dzf = zh[1:] - zh[:-1]


# print (len(dzf), len(zh), len(rhof[0,:]))
#print ('dzf', dzf)
ldzf = len(dzf)
rwp = numpy.sum(qr[:,0:ldzf] * rhof[:,0:ldzf] * dzf[:], axis=1)  # rwp over time
#print ('rwp', rwp)

imin, l = sel_range(time2)
print('Averaging from %.1f to %.1f h'%(time2[imin]/3600, time2[-1]/3600))


prec_avg = numpy.mean(prec[imin:l])
rwp_avg = numpy.mean(rwp[imin:l])

qr_avg     = numpy.mean(qr[imin:l], axis=0)
ql_avg     = numpy.mean(ql[imin:l], axis=0)
qt_avg     = numpy.mean(qt[imin:l], axis=0)
thl_avg    = numpy.mean(thl[imin:l], axis=0)
u_avg      = numpy.mean(u[imin:l], axis=0)
v_avg      = numpy.mean(v[imin:l], axis=0)
zcfrac_avg = numpy.mean(zcfrac[imin:l], axis=0)

# get wall clock time from output file
def get_walltime(filename):
    try:
        t = tail(filename, 1)[0]
        return float(t.split(b'=')[-1])
    except:
        return None
    
# extract wallclock time from output text file.
# try several possibilities for the output file name
out_files = glob.glob("output.txt")
out_files.extend(glob.glob("*.output"))
walltime = get_walltime(out_files[0])
print('output file:', out_files[0], 'walltime:', walltime)

with open('results.csv', 'wt') as out_file:
    # needs one row of headers, then row(s) of data
    # spaces not allowed in column names (or the space becomes part of the name)
    print("cfrac,lwp,rwp,zb,zi,prec,wq,wtheta,we,walltime", file=out_file)
    print(f"{gcfrac_avg},{lwp_bar_avg},{rwp_avg},{zb_avg},{zi_avg},{prec_avg},{wq_avg},{wtheta_avg},{we_avg},{walltime}", file=out_file)



# JSON output - can also include vertical profiles
results = {'cfrac' : float(gcfrac_avg),
           'lwp' : float(lwp_bar_avg),
           'rwp' : float(rwp_avg),
           'zb' : float(zb_avg),
           'zi' : float(zi_avg),
           'prec' : float(prec_avg),
           'wq' : float(wq_avg),
           'wtheta' : float(wtheta_avg),
           'we' : float(we_avg),
           'qr' : qr_avg.tolist(),
           'ql' : ql_avg.tolist(),
           'qt' : qt_avg.tolist(),
           'thl' : thl_avg.tolist(),
           'u' : u_avg.tolist(),
           'v' : v_avg.tolist(),
           'zcfrac' : zcfrac_avg.tolist(),
           'walltime' : walltime,
}

#print(results)
with open('results.json', 'w') as out_file:
    json.dump(results, out_file, indent=2)




