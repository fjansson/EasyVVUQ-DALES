import os
import subprocess
import argparse
import easyvvuq as uq
import chaospy as cp



# Trying DALES with EasyVVUQ
# based on EasyVVUQ gauss tutorial
# Fredrik Jansson Nov. 2019

# 0. Setup some variables describing app to be run
#
#    gauss.py is in current directory and takes one input file
#    and writes to 'output.csv'.
dales_exe = "~/dales/build/src/dales4"
cwd = os.getcwd()
input_filename = 'namoptions.001'
cmd = f"{dales_exe} {input_filename}"
out_file = "results.csv"
postproc="postproc.py"
work_dir="/export/scratch3/jansson/uq-work/"
state_file_name="campaign_state.json"

# Template input to substitute values into for each run
template = f"{cwd}/namoptions.template"
#template = f"{cwd}/namoptions-1h-10x10.template"


# Parameter handling 
parser = argparse.ArgumentParser(description="EasyVVUQ for DALES")
parser.add_argument("--prepare",  action="store_true", default=False,
                    help="Prepare run directories")
parser.add_argument("--run",  action="store_true", default=False,
                    help="Run model, sequentially")
parser.add_argument("--analyze",  action="store_true", default=False,
                    help="Analyze results")
parser.add_argument("--sampler",  default="sc", choices=['sc', 'pce'],
                    help="UQ sampling method, sc is the default.")
parser.add_argument("--order",  default="2", type=int,
                    help="Sampler order")

args = parser.parse_args()

# 2. Parameter space definition
params = {
    "Nc_0": {
        "type": "float",
        "min": 0.1e6,
        "max": 1000e6,
        "default": 70e6,
#        "unit" : "m^-3"
    },
    "cf": {  # cf subgrid filter constant
        "type": "float",
        "min": 1.0,     # min, max are just guesses 
        "max": 4.0,  
        "default": 2.5,
#        "unit" : ""
    },
    "cn": {  # Subfilterscale parameter
        "type": "float",
        "min": 0.5,     # min, max are just guesses 
        "max": 1.0,  
        "default": 0.76,
#        "unit" : ""
    },
    "Rigc": {  # Critical Richardson number
        "type": "float",
        "min": 0.1,     # min, max are just guesses 
        "max": 1.0,  
        "default": 0.25,
#        "unit" : ""
    },
    "Prandtl": {  # Prandtl number, subgrid.
        "type": "float",
        "min": 0.1,     # min, max are just guesses 
        "max": 1.0,  
        "default": 1.0/3,
#        "unit" : ""
    },
    "z0": {            # surface roughness  
        "type": "float",
        "min": 1e-4,     # min, max are just guesses 
        "max": 1.0,  
        "default": 1.6e-4,
#        "unit" : "m"
    },
}

# can't have extra fields in params dict.

vary = {
    "Nc_0"    : cp.Uniform(50e6, 100e6),
    "cf"      : cp.Uniform(2.4, 2.6),
#    "cn"      : cp.Uniform(0.5, 0.9),
#    "Rigc"    : cp.Uniform(0.1, 0.4),
    "Prandtl" : cp.Uniform(0.2, 0.4),
#    "z0"      : cp.Uniform(1e-4, 2e-4),
}



output_columns = ['cfrac', 'lwp', 'rwp', 'zb', 'zi', 'prec', 'wq', 'wtheta', 'we']
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

    'z0' : 'm',
    'Nc_0' : 'm^-3',
}

# 4. Specify Sampler
if args.sampler=='sc':
    my_sampler = uq.sampling.SCSampler(vary=vary, polynomial_order=args.order,
                                       quadrature_rule="G")
elif args.sampler=='pce':
    my_sampler = uq.sampling.PCESampler(vary=vary, polynomial_order=args.order,
                                        quadrature_rule="G")

    
if args.prepare:
    # 1. Create campaign
    my_campaign = uq.Campaign(name='dales', work_dir=work_dir)
    # all run directories created under workdir

    # 3. Wrap Application
    #    - Define a new application (we'll call it 'gauss'), and the encoding/decoding elements it needs
    #    - Also requires a collation element - this will be responsible for aggregating the results
    encoder = uq.encoders.GenericEncoder(template_fname=template,
                                     target_filename=input_filename)
    decoder = uq.decoders.SimpleCSV(
        target_filename=out_file,
        output_columns=output_columns,
        header=0)

    collater = uq.collate.AggregateSamples(average=False)

    my_campaign.add_app(name="dales",
                        params=params,
                        encoder=encoder,
                        decoder=decoder,
                        collater=collater
    )

    my_campaign.set_sampler(my_sampler)
    
    # 5. Get run parameters
    my_campaign.draw_samples()

    # 6. Create run input directories
    my_campaign.populate_runs_dir()


    print(my_campaign)

    # 7. Run Application
    #    - dales is executed for each sample
    
    link=f"link.sh {cwd+'/input'}"

    my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(link))
    
    my_campaign.save_state(state_file_name)

################################################


if args.run:
    my_campaign = uq.Campaign(state_file=state_file_name, work_dir=work_dir)

    # run sequentially
    # my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(cmd))

    pcmd = "ls -d %s/runs/Run_* | parallel -j 12 'cd {} ; ~/dales/build/src/dales4 namoptions.001 > output.txt ;  cd .. '"%my_campaign.campaign_dir
    print ('Parallel run command', pcmd)
    subprocess.call(pcmd, shell=True)
    my_campaign.save_state(state_file_name)

################################################

if args.analyze:
    my_campaign = uq.Campaign(state_file=state_file_name, work_dir=work_dir)


    my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(postproc, interpret='python3'))

    # 8. Collate output
    my_campaign.collate()

    # 9. Run Analysis
    if args.sampler == 'sc':
        analysis = uq.analysis.SCAnalysis(sampler=my_sampler, qoi_cols=output_columns)
    elif args.sampler == 'pce':
        analysis = uq.analysis.PCEAnalysis(sampler=my_sampler, qoi_cols=output_columns)

    my_campaign.apply_analysis(analysis)
    results = my_campaign.get_last_analysis()

    if args.sampler == 'sc':  # multi-var Sobol indices are not available for PCE
        for qoi in output_columns: 
            print(qoi, results['statistical_moments'][qoi]['mean'], 
                  results['statistical_moments'][qoi]['std'],
                  'sobols:', results['sobols'][qoi],
            ) #'sobols_first:', results['sobols_first'][qoi])




    print(f"sampler: {args.sampler}, order: {args.order}")
    print('         --- Varied input parameters ---')
    print("  param    default      unit     distribution")
    for k in vary.keys():
        print("%8s %9.3g %9s  %s"%(k, params[k]['default'], unit.get(k, ''), str(vary[k])))
    print()

    print('         --- Output ---')
    var = list(vary.keys())

    print("                                            Sobol indices")
    print("       QOI      mean       std      unit  ", end='')
    for v in var:
        print('%9s'%v, end=' ')
    print()

    for qoi in output_columns:
        print("%10s"%qoi, end=' ')
        print("% 9.3g % 9.3g"%(results['statistical_moments'][qoi]['mean'], results['statistical_moments'][qoi]['std']), end=' ')
        print("%9s"%unit[qoi], end='  ')
        for v in var:
            print('%9.3g'%results['sobols_first'][qoi][v], end=' ')
        print()
    
    

    



