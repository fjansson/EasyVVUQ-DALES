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

# compute means over last half of simulation
l = len(cfrac)
cfrac_avg = numpy.mean(cfrac[l//2:l])
lwp_bar_avg = numpy.mean(lwp_bar[l//2:l])
zb_avg = numpy.mean(lwp_bar[l//2:l])

p = Dataset("profiles.001.nc", 'r')
prec = p.variables["precmn"][:,0]
l = len(prec)
prec_avg = numpy.mean(prec[l//2:l])

out_file = open('results.csv', 'wt')

# needs one row of headers, then row(s) of data
# spaces not allowed(?)
print("cfrac,lwp,zb,prec", file=out_file)
print(f"{cfrac_avg},{lwp_bar_avg},{zb_avg},{prec_avg}", file=out_file)



# did this anticipating json output
# but there is no decoder for that
results = {'cfrac' : cfrac_avg,
           'lwp' : lwp_bar_avg,
           'zb' : zb_avg,
           'prec' : prec_avg,
}

print(results)

