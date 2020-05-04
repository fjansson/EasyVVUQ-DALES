import os
import subprocess
import argparse
import sys
import easyvvuq as uq
import chaospy as cp
import matplotlib.pyplot as plt
from easyvvuq.decoders.json import JSONDecoder
from easyvvuq.encoders.jinja_encoder import JinjaEncoder
import fabsim3_cmd_api as fab
import numpy

# Analyzing DALES with EasyVVUQ
# based on EasyVVUQ gauss tutorial
# Fredrik Jansson, CWI, 2019-2020

# 0. Setup some variables describing app to be run

cwd = os.getcwd()
input_filename = 'namoptions.001'
#out_file = "results.json"; use_csv_decoder=False
out_file = "results.csv"; use_csv_decoder=True

postproc="postproc.py"

# Parameter handling 
parser = argparse.ArgumentParser(description="EasyVVUQ for DALES",
                                 fromfile_prefix_chars='@')
parser.add_argument("--prepare",  action="store_true", default=False,
                    help="Prepare run directories")
parser.add_argument("--run",  action="store_true", default=False,
                    help="Run model, sequentially")
parser.add_argument("--parallel", type=int, default=0,
                    help="use parallel command to run model with N threads")
parser.add_argument("--fab", action="store_true", default=False,
                    help="use Fabsim to run model")
parser.add_argument("--analyze",  action="store_true", default=False,
                    help="Analyze results")
parser.add_argument("--sampler",  default="sc", choices=['sc', 'pce', 'random'],
                    help="UQ sampling method, sc is the default.")
parser.add_argument("--num_samples",  default="10", type=int,
                    help="number of samples for the random sampler.")
parser.add_argument("--order",  default="2", type=int,
                    help="Sampler order")
parser.add_argument("--model",  default="dales4", help="Model executable file")
parser.add_argument("--workdir", default="/tmp", help="Model working directory base")
parser.add_argument("--template", default="namoptions.template", help="Template for model input file")
parser.add_argument("--campaign", default="campaign_state.json", help="Campaign state file name")
parser.add_argument("--replicas", default="1", type=int, help="Number of replicas")
parser.add_argument("--experiment", default="physics", help="experiment setup - chooses set of parameters to vary")

args = parser.parse_args()
template = os.path.abspath(args.template)


print ("workdir:",args.workdir)

# 2. Parameter space definition
params = {
    "Nc_0": {
        "type": "float",
        "min": 0.1e6,
        "max": 1000e6,
        "default": 70e6,
    },
    "cf": {  # cf subgrid filter constant
        "type": "float",
        "min": 1.0,     # min, max are just guesses
        "max": 4.0,
        "default": 2.5,
    },
    "cn": {  # Subfilterscale parameter
        "type": "float",
        "min": 0.5,     # min, max are just guesses
        "max": 1.0,
        "default": 0.76,
    },
    "Rigc": {  # Critical Richardson number
        "type": "float",
        "min": 0.1,     # min, max are just guesses
        "max": 1.0,
        "default": 0.25,
    },
    "Prandtl": {  # Prandtl number, subgrid.
        "type": "float",
        "min": 0.1,     # min, max are just guesses
        "max": 1.0,
        "default": 1.0/3,
    },
    "z0": {            # surface roughness  - note: if z0mav, z0hav are specified, they will override z0
        "type": "float", 
        "min": 1e-4,     # min, max are just guesses
        "max": 1.0,
        "default": 1.6e-4,
    },
    "l_sb": { # flag for microphysics scheme: false - KK00 Khairoutdinov and Kogan, 2000
        "type": "float",                   #   true - SB   Seifert and Beheng, 2001, 2006, Default
        "min" : 0,
        "max" : 1,
        "default": 1
    },
    "seed":{
        "type": "float",   # random seed
        "min" : 1,
        "max" : 1000000,
        "default" : 43
    },
    "poissondigits": {   # precision of the iterative Poisson solver. tolerance=10**-poissondigits
        "type": "float", # only useful if the template contains a &solver section
        "min": 1,
        "max": 16,
        "default": 15,
    },
    "ps": { # surface pressure, Pa
        "type": "float",
        "min": 90000,
        "max": 110000,
        "default": 101540.00,
    },
    "thls": { # surface temperature, K
        "type": "float",
        "min": 270,
        "max": 320,
        "default": 298.5,
    },
    "iadv": {
        "type": "float",
        "min": 0,
        "max": 1,
        "default": 0,
    },
    "iadv_sv": {
        "type": "float",
        "min": 0,
        "max": 2,
        "default": 2,
    },
}

vary_physics_test = {  # Physics - preliminary run
    "Nc_0"    : cp.Uniform(50e6, 100e6),
    "cf"      : cp.Uniform(2.4, 2.6),
#    "cn"      : cp.Uniform(0.5, 0.9),
#    "Rigc"    : cp.Uniform(0.1, 0.4),
    "Prandtl" : cp.Uniform(0.2, 0.4),
#    "z0"      : cp.Uniform(1e-4, 2e-4),
#    "l_sb"    :  cp.DiscreteUniform(0, 1),
    "seed"    : cp.DiscreteUniform(1, 2000),
}


vary_physics = {  # Physics 
    "seed"    : cp.DiscreteUniform(1, 2000),
    "Nc_0"    : cp.Uniform(50e6, 100e6),
    "thls"    : cp.Uniform(298, 299),
#    "z0"      : cp.LogUniform(numpy.log(1e-4),numpy.log(1e-1))    
#    "cf"      : cp.Uniform(2.4, 2.6),
#    "cn"      : cp.Uniform(0.5, 0.9),
#    "Rigc"    : cp.Uniform(0.1, 0.4),
#    "Prandtl" : cp.Uniform(0.2, 0.4),
#    "z0"      : cp.Uniform(1e-4, 2e-4),
#    "l_sb"    :  cp.DiscreteUniform(0, 1),
}

vary_physics_z0 = {  # Physics 
    "seed"    : cp.DiscreteUniform(1, 2000),
    "Nc_0"    : cp.Uniform(50e6, 100e6),
    "thls"    : cp.Uniform(298, 299),
    "z0"      : cp.LogUniform(numpy.log(1e-4),numpy.log(1e-1))    # note: has effect if z0hav, z0mav are not in namelist
#    "cf"      : cp.Uniform(2.4, 2.6),
#    "cn"      : cp.Uniform(0.5, 0.9),
#    "Rigc"    : cp.Uniform(0.1, 0.4),
#    "Prandtl" : cp.Uniform(0.2, 0.4),
#    "z0"      : cp.Uniform(1e-4, 2e-4),
#    "l_sb"    :  cp.DiscreteUniform(0, 1),

}

vary_choices = {  # microphysics choice, advection scheme
    "l_sb"    : cp.DiscreteUniform(0, 1),  # 0 - false, 1 - true
    "iadv"    : cp.DiscreteUniform(0, 1),  # 0 - 2nd order, 1 - 5th order
    "iadv_sv" : cp.DiscreteUniform(0, 2),  # 0 - 2nd order, 1 - 5th order, 2 - kappa scheme
    "seed"    : cp.DiscreteUniform(1, 2000),
}

# note use .poisson template which has iterative solver
vary_poisson = {
    "seed"    : cp.DiscreteUniform(1, 2000),
    "poissondigits": cp.Uniform(2,13)
    # rico, 112x112 cells, 24 h did not converge when poissondigits >= 14
}

vary_test = {  
    "Nc_0"    : cp.Uniform(50e6, 100e6),
    "seed"    : cp.DiscreteUniform(1, 2000),
}

experiment_options = {
    'physics_z0' : (vary_physics_z0, (3, 3, 3, 3)), # physics including z0
    'physics'    : (vary_physics, (5, 5, 5)),         # physics without z0
    'poisson'    : (vary_poisson, (4, 6)),
    'test'       : (vary_test,    (2, 2)),
    'choices'    : (vary_choices, (2,2,3,5))    # advection and microphysics schemes
}

vary, order = experiment_options[args.experiment]
print('Parameters chosen for variation:', vary)

output_columns = ['cfrac', 'lwp', 'rwp', 'zb', 'zi', 'prec', 'wq', 'wtheta', 'we', 'walltime']
unit={
     'cfrac' :'',
     'lwp'   :'g/m$^2$',
     'rwp'   :'g/m$^2$',
     'zb'    :'m',
     'zi'    :'m',
     'prec'  :'W/m$^2$',
     'wq'    :'kg/kg m/s',
     'wtheta':'K m/s',
     'we'    :'m/s',

     'z0'    :'m',
     'Nc_0'  :'m$^{-3}$',
     'walltime':'s',
     'ps'      :'Pa',
     'thls'    :'K',
}

scale={ 
    'lwp'    : 1000,  # convert kg/m^2 to g/m^2
    'rwp'    : 1000,  # convert kg/m^2 to g/m^2
}

# different polynomial order in different dimensions
# use to avoid repeating integer parameters with small range
#order = [args.order] * len(vary)
#for i,k in enumerate(vary):
#    #print(i, k, params[k])
#    if (params[k]["type"] == "integer"):
#        max_order = (params[k]["max"] - params[k]["min"])
#        order[i] = min(order[i],max_order)


print(f'Orders: {order} (only for SC sampler)')


    
# 4. Specify Sampler
if args.sampler=='sc':
    # sc sampler can have differet orders for different dimensions
    my_sampler = uq.sampling.SCSampler(vary=vary, polynomial_order=order,
                                       quadrature_rule="C")
elif args.sampler=='pce':
    print('order argument',args.order)
    my_sampler = uq.sampling.PCESampler(vary=vary, polynomial_order=args.order)
                                        # quadrature_rule="G")
elif args.sampler=='random':
    my_sampler = uq.sampling.RandomSampler(vary=vary)
else:
    print("Unknown sampler specified", args.sampler)
    sys.exit()
    

    
if args.prepare:
    # 1. Create campaign
    my_campaign = uq.Campaign(name='dales',  work_dir=args.workdir)

    # all run directories, and the database are created under workdir
    
    # json database can contain vector-valued QoI's.  - gone since 22.4.2020
    # the default sql database cannot, at the moment.

    # 3. Wrap Application
    #    - Define a new application, and the encoding/decoding elements it needs
    #    - Also requires a collation element - this will be responsible for aggregating the results

#    encoder = uq.encoders.GenericEncoder(template_fname=template,
#                                         target_filename=input_filename)
    encoder = JinjaEncoder(template_fname=template,
                           target_filename=input_filename)
    if use_csv_decoder:    
        decoder = uq.decoders.SimpleCSV(
            target_filename=out_file,
            output_columns=output_columns,
            header=0)
    else:
        decoder = JSONDecoder(
            target_filename=out_file,
            output_columns=output_columns)
        
    collater = uq.collate.AggregateSamples(average=False)

    my_campaign.add_app(name="dales",
                        params=params,
                        encoder=encoder,
                        decoder=decoder,
                        collater=collater
    )

    my_campaign.set_sampler(my_sampler)

    if args.experiment=='choices':
        my_campaign.verify_all_runs = False
    # to prevent validation errors on integer quantities
    # better work-around: declare the parameters with float data type even if they are integer-valued
    
    # 5. Get run parameters
    if args.sampler=='random':
        my_campaign.draw_samples(num_samples=args.num_samples, replicas=args.replicas)
    else:
        my_campaign.draw_samples(replicas=args.replicas)

    # 6. Create run input directories
    my_campaign.populate_runs_dir()

    print(my_campaign)

    # 7. Run Application
    #    - dales is executed for each sample
    
    link=f"prep.sh {cwd+'/input'}"

    my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(link))
    
    my_campaign.save_state(args.campaign)

################################################

if args.run:
    my_campaign = uq.Campaign(state_file=args.campaign, work_dir=args.workdir)

    # run sequentially
    # my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(cmd))
    
    if args.parallel:
        pcmd = f"ls -d {my_campaign.campaign_dir}/runs/Run_* | parallel -j {args.parallel} 'cd {{}} ; {args.model} namoptions.001 > output.txt ;  cd .. '"
        print ('Parallel run command', pcmd)
        subprocess.call(pcmd, shell=True)
    elif args.fab:
        fab.run_uq_ensemble(my_campaign.campaign_dir, script_name='dales', machine='eagle_vecma')
    else:
        my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(f"{args.model} namoptions.001 > output.txt"))
        
    my_campaign.save_state(args.campaign)

################################################

if args.analyze:
    my_campaign = uq.Campaign(state_file=args.campaign, work_dir=args.workdir)

    if args.fab:
        print("Fetching results with FabSim:")
        fab.get_uq_samples(my_campaign.campaign_dir, machine='eagle_vecma')
        
    my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(postproc, interpret='python3'))

    # 8. Collate output
    my_campaign.collate()

    data = my_campaign.get_collation_result()
    print(data)
#    print(type(data['qt'][0]))
#    print(data['qt'][0])

    
    # 9. Run Analysis
    if args.sampler == 'random':
        analysis = uq.analysis.BasicStats(qoi_cols=output_columns)
        my_campaign.apply_analysis(analysis)
        print("stats:\n", my_campaign.get_last_analysis())
        sys.exit()

    if args.sampler == 'sc':
        analysis = uq.analysis.SCAnalysis(sampler=my_sampler, qoi_cols=output_columns)
    elif args.sampler == 'pce':
        analysis = uq.analysis.PCEAnalysis(sampler=my_sampler, qoi_cols=output_columns)    
    
    my_campaign.apply_analysis(analysis)
    results = my_campaign.get_last_analysis()

    print('Analysis: analysis.get_sample_array()')
    print(analysis.get_sample_array('prec'))
    print()
    
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

    print("                                                  Sobol indices")
    print("       QOI      mean       std  std(%)     unit  ", end='')
    for v in var:
        print('%9s'%v, end=' ')
    print()

    for qoi in output_columns:
        print("%10s"%qoi, end=' ')
        print("% 9.3g % 9.3g % 6.1f"%(results['statistical_moments'][qoi]['mean'] * scale.get(qoi,1),
                                      results['statistical_moments'][qoi]['std'] * scale.get(qoi,1),
                                      100*results['statistical_moments'][qoi]['std']/results['statistical_moments'][qoi]['mean']),
              end=' ')
        print("%9s"%unit[qoi], end='  ')
        for v in var:
            print('%9.3g'%results['sobols_first'][qoi][v], end=' ')
        print()
    
    

    # print(analysis.get_sample_array('cfrac'))  # just the sample values, no coordinates.
    # print(my_campaign.get_collation_result()) # a Pandas dataframe

    scalar_outputs = output_columns # [:-1]
    #plt.plot(data['Nc_0'], data['prec'], 'o')
    params = vary.keys()
    fig, ax = plt.subplots(nrows=len(scalar_outputs), ncols=len(params),
                        sharex='col', sharey='row', squeeze=False)

    for i,param in enumerate(params):
        for j,qoi in enumerate(scalar_outputs):
            x = data[param] * scale.get(param,1)
            y = data[qoi]   * scale.get(qoi,1)
            ax[j][i].plot(x, y, 'o')
            xu = unit.get(param,'')
            yu = unit.get(qoi,'')
            if xu: xu = f"({xu})"
            if yu: yu = f"({yu})"
            ax[j][i].set(xlabel=f"{param} {xu}", ylabel=f"{qoi}\n{yu}")

    for a in ax.flat:
        a.label_outer()
        a.ticklabel_format(axis='y', style='sci', scilimits=(-5,5), useOffset=None, useLocale=None, useMathText=True)            
    plt.show()
