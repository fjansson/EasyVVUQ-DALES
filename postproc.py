#!/usr/bin/env python3

# quick post-processor for UQ of DALES runs
# reads DALES output files, extracts interesting
# quantities, averages them over last half of the run.
# Writes output to results.csv

from netCDF4 import Dataset
import numpy

d = Dataset("tmser.001.nc", 'r')

cfrac   = d.variables['cfrac'][:]
lwp_bar = d.variables['lwp_bar'][:]
zb = d.variables['zb'][:]
zi = d.variables['zi'][:]
wq = d.variables['wq'][:]
wtheta = d.variables['wtheta'][:]
we = d.variables['we'][:]

# compute means over last half of simulation
l = len(cfrac)
cfrac_avg = numpy.mean(cfrac[l//2:l])
lwp_bar_avg = numpy.mean(lwp_bar[l//2:l])
zb_avg = numpy.mean(zb[l//2:l])
zi_avg = numpy.mean(zi[l//2:l])
wq_avg = numpy.mean(wq[l//2:l])
wtheta_avg = numpy.mean(wtheta[l//2:l])
we_avg = numpy.mean(we[l//2:l])

p = Dataset("profiles.001.nc", 'r')
# precipitation flux at lowest level
prec    = p.variables["precmn"][:,0]  
qr_prof = p.variables["sv002"][:,:]
rhof    = p.variables["rhof"][:,:]
zh      = p.variables["zm"][:]  # half-level heights  # dzf(k) = zh(k+1) - zh(k)
dzf = zh[1:] - zh[:-1]

# print (len(dzf), len(zh), len(rhof[0,:]))
#print ('dzf', dzf)
ldzf = len(dzf)
rwp = numpy.sum(qr_prof[:,0:ldzf] * rhof[:,0:ldzf] * dzf[:], axis=1)  # rwp over time
#print ('rwp', rwp)

l = len(prec)
prec_avg = numpy.mean(prec[l//2:l])
rwp_avg = numpy.mean(rwp[l//2:l])
out_file = open('results.csv', 'wt')



# needs one row of headers, then row(s) of data
# spaces not allowed(?)
print("cfrac,lwp,rwp,zb,zi,prec,wq,wtheta,we", file=out_file)
print(f"{cfrac_avg},{lwp_bar_avg},{rwp_avg},{zb_avg},{zi_avg},{prec_avg},{wq_avg},{wtheta_avg},{we_avg}", file=out_file)



# did this anticipating json output
# but there is no decoder for that
results = {'cfrac' : cfrac_avg,
           'lwp' : lwp_bar_avg,
           'rwp' : rwp_avg,
           'zb' : zb_avg,
           'zi' : zi_avg,
           'prec' : prec_avg,
           'wq' : wq_avg,
           'wtheta' : wtheta_avg,
           'we' : we_avg,
}

print(results)

