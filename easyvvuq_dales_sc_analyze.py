import os
import easyvvuq as uq
import chaospy as cp

# Trying DALES with EasyVVUQ
# based on EasyVVUQ gauss tutorial
# Fredrik Jansson Nov. 2019


# runs analysis after runs have been completed

# 0. Setup some variables describing app to be run
#    
#    and writes to 'output.csv'.
dales_exe = "~/code/official-dales/build/src/dales4"
cwd = os.getcwd()
input_filename = 'namoptions.001'
cmd = f"{dales_exe} {input_filename}"
out_file = "results.csv"
work_dir="/tmp"


# 2. Parameter space definition
params = {
    "Nc_0": {
        "type": "float",
        "min": 0.1e6,
        "max": 1000e6,
        "default": 70e6,
        "unit" : "m^-3"
    },
    "cf": {  # cf subgrid filter constant
        "type": "float",
        "min": 1.0,     # min, max are just guesses 
        "max": 4.0,  
        "default": 2.5,
        "unit" : ""
    },
    "Prandtl": {  # Prandtl number, subgrid.
        "type": "float",
        "min": 0.1,     # min, max are just guesses 
        "max": 1.0,  
        "default": 1.0/3,
        "unit" : ""
    },
    "z0": {            # surface roughness  
        "type": "float",
        "min": 1e-4,     # min, max are just guesses 
        "max": 1.0,  
        "default": 1.6e-4,
        "unit" : "m"
    },
}

vary = {
    "Nc_0"    : cp.Uniform(50e6, 100e6),
    "cf"      : cp.Uniform(2.4, 2.6),
    "Prandtl" : cp.Uniform(0.2, 0.4),
    "z0"      : cp.Uniform(1e-4, 2e-4), 
}

output_columns = ['cfrac', 'lwp', 'rwp', 'zb', 'zi', 'prec', 'wq', 'wtheta', 'we']

my_campaign = uq.Campaign(state_file="campaign_state.json", work_dir=work_dir)

my_sampler = uq.sampling.SCSampler(vary=vary, polynomial_order=2,
                                   quadrature_rule="G")

postproc="postproc.py"
my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(postproc, interpret='python3'))

# 8. Collate output
my_campaign.collate()

# 9. Run Analysis
analysis = uq.analysis.SCAnalysis(sampler=my_sampler, qoi_cols=output_columns)

my_campaign.apply_analysis(analysis)

results = my_campaign.get_last_analysis()

for qoi in output_columns:
    print(qoi, results['statistical_moments'][qoi]['mean'], 
               results['statistical_moments'][qoi]['std'],
               'sobols:', results['sobols'][qoi],
               )#'sobols_first:', results['sobols_first'][qoi])


unit={
     'cfrac' :'',
     'lwp'   :'kg/m^2',
     'rwp'   :'kg/m^2',
     'zb'    :'m',
     'zi'    :'m',
     'prec'  : 'W/m^2',
     'wq'    :'kg/kg m/s',
     'wtheta':'K m/s',
     'we'    :'m/s',      
}

var = list(vary.keys())
print()
print("                                          Sobol indices")
print("       QOI      mean       std      unit  ", end='')
for v in var:
    print('%6s'%v, end=' ')
print()

for qoi in output_columns:
    print("%10s"%qoi, end=' ')
    print("% 9.3g % 9.3g"%(results['statistical_moments'][qoi]['mean'], results['statistical_moments'][qoi]['std']), end=' ')
    print("%9s"%unit[qoi], end='  ')
    for v in var:
        print('%6.4g'%results['sobols_first'][qoi][v], end=' ')
    print()
    
    

    
