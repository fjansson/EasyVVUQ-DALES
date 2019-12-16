#!/usr/bin/env python3

# quick post-processor for UQ of DALES runs
# reads DALES output files, extracts interesting
# quantities, averages them over last half of the run.
# Writes output to results.csv

import numpy
import json
from netCDF4 import Dataset
import subprocess


# https://stackoverflow.com/a/136280/1333273
def tail(f, n):
    proc = subprocess.Popen(['tail', '-n', str(n), f], stdout=subprocess.PIPE)
    lines = proc.stdout.readlines()
    return lines


d = Dataset("tmser.001.nc", 'r')

gcfrac   = d.variables['cfrac'][:]     # global cloud fraction
lwp_bar = d.variables['lwp_bar'][:]
zb = d.variables['zb'][:]
zi = d.variables['zi'][:]
wq = d.variables['wq'][:]
wtheta = d.variables['wtheta'][:]
we = d.variables['we'][:]

# compute means over last half of simulation
l = len(gcfrac)
gcfrac_avg = numpy.mean(gcfrac[l//2:l])
lwp_bar_avg = numpy.mean(lwp_bar[l//2:l])
zb_avg = numpy.mean(zb[l//2:l])
zi_avg = numpy.mean(zi[l//2:l])
wq_avg = numpy.mean(wq[l//2:l])
wtheta_avg = numpy.mean(wtheta[l//2:l])
we_avg = numpy.mean(we[l//2:l])

p = Dataset("profiles.001.nc", 'r')
# precipitation flux at lowest level
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

l = len(prec)
prec_avg = numpy.mean(prec[l//2:l])
rwp_avg = numpy.mean(rwp[l//2:l])

qr_avg     = numpy.mean(qr[l//2:l], axis=0)
ql_avg     = numpy.mean(ql[l//2:l], axis=0)
qt_avg     = numpy.mean(qt[l//2:l], axis=0)
thl_avg    = numpy.mean(thl[l//2:l], axis=0)
u_avg      = numpy.mean(u[l//2:l], axis=0)
v_avg      = numpy.mean(v[l//2:l], axis=0)
zcfrac_avg = numpy.mean(zcfrac[l//2:l], axis=0)


# get wall clock time from output file
walltime = -1
try:
    t = tail('output.txt', 1)[0]
    walltime = float(t.split(b'=')[-1])
except:
    pass

# print ('tail', t, 'walltime', walltime)

with open('results.csv', 'wt') as out_file:
    # needs one row of headers, then row(s) of data
    # spaces not allowed in column names (or the space becomes part of the name)
    print("cfrac,lwp,rwp,zb,zi,prec,wq,wtheta,we,walltime", file=out_file)
    print(f"{gcfrac_avg},{lwp_bar_avg},{rwp_avg},{zb_avg},{zi_avg},{prec_avg},{wq_avg},{wtheta_avg},{we_avg},{walltime}", file=out_file)



# did this anticipating json output  (but there is no decoder for that)
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




