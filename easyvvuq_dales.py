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
import numpy.random

# Analyzing DALES with EasyVVUQ
# based on the EasyVVUQ gauss tutorial
# Fredrik Jansson, CWI, 2019-2020

# 0. Setup some variables describing app to be run

cwd = os.getcwd()
input_filename = 'namoptions.001'
out_file = "results.csv"; use_csv_decoder=True
#out_file = "results.json"; use_csv_decoder=False # uncomment to use JSON-format results file
                                                  # which supports vector-valued QoIs (in progress)

postproc = "postproc.py" # post-processing script, run after DALES for each sample

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
parser.add_argument("--fetch",  action="store_true", default=False,
                    help="Fetch fabsim results")
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
parser.add_argument("--plot", default=None, type=str, help="File name for plot")

args = parser.parse_args()
template = os.path.abspath(args.template)
print ("workdir:",args.workdir)

# 2. Parameter space definition. List of parameters that can be varied.
# (which parameters are actually varied in a single experiment is defined
# further below, vary = ...)
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
        "min": 0.4,     # min, max are just guesses
        "max": 1.0,
        "default": 0.76,
    },
    "Rigc": {  # Critical Richardson number
        "type": "float",
        "min": 0.09,     # min, max are just guesses
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
        "min": 1e-4,     
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

# The following is a list of experiment definitions, one of which can be
# selectend with the --experiment command line switch.

# vary physical quantities
# note: z0 has effect if z0hav, z0mav are not in namelist - use namoptions-z0.template
vary_physics_z0 = {
    "seed"    : cp.DiscreteUniform(1, 2000),
    "Nc_0"    : cp.Uniform(50e6, 100e6),
    "thls"    : cp.Uniform(298, 299),
    "z0"      : cp.Uniform(1e-4, 2e-4),
}

# vary subgrid scheme parameters
vary_subgrid = {
    "seed"    : cp.DiscreteUniform(1, 2000),
    "cn"      : cp.Uniform(0.5, 0.9),  # default 0.76         
    "Rigc"    : cp.Uniform(0.1, 0.4),  # default 0.25
    "Prandtl" : cp.Uniform(0.2, 0.4),  # default 1/3
}

# vary microphysics choice, advection scheme
vary_choices = {  
    "l_sb"    : cp.DiscreteUniform(0, 1),  # 0 - false, 1 - true
    "iadv"    : cp.DiscreteUniform(0, 1),  # 0 - 2nd order, 1 - 5th order
    "iadv_sv" : cp.DiscreteUniform(0, 2),  # 0 - 2nd order, 1 - 5th order, 2 - kappa scheme
    "seed"    : cp.DiscreteUniform(1, 2000),
}

# vary Poisson solver tolerance
# note use namoptions.poisson template which has iterative solver
vary_poisson = {
    "seed"    : cp.DiscreteUniform(1, 2000),
    "poissondigits": cp.Uniform(2,13)
    # the iteration doesn't always converge when poissondigits >= 14
}

# small test run
vary_test = {  
    "Nc_0"    : cp.Uniform(50e6, 100e6),
    "seed"    : cp.DiscreteUniform(1, 2000),
}

# map --experiment option to a dictionary of parameters to vary, and the polynomial order
# for each parameter. The number of samples along each parameter dimension is (order + 1)
# for the SC method.
experiment_options = {
    'physics_z0' : (vary_physics_z0, (3, 3, 3, 3)), # physics including z0
    'poisson'    : (vary_poisson, (4, 6)),
    'test'       : (vary_test,    (2, 2)),
    'choices'    : (vary_choices, (2,2,3,5)),    # advection and microphysics schemes
    'subgrid'    : (vary_subgrid, (2,2,2,2)),      
}

vary, order = experiment_options[args.experiment]
print('Parameters chosen for variation:', vary)

# list of model output quantities of interest (QoIs) to analyze
output_columns = ['cfrac', 'lwp', 'rwp', 'zb', 'zi', 'prec', 'wq', 'wtheta', 'walltime']
# omitted to save space: we

# dictionary of units of the different quantities
unit={
     'cfrac' :'',
     'lwp'   :'g/m$^2$',
     'rwp'   :'g/m$^2$',
     'zb'    :'km',
     'zi'    :'km',
     'prec'  :'W/m$^2$',
     'wq'    :'g/kg m/s',
     'wtheta':'K m/s',
     'we'    :'m/s',
     'z0'    :'mm',
     'Nc_0'  :'cm$^{-3}$',
     'walltime':'h',
     'ps'      :'Pa',
     'thls'    :'K',
}

# unit conversion for some quantities for nicer display
scale={ 
    'lwp'      : 1000,     # convert kg/m^2 to g/m^2
    'rwp'      : 1000,     # convert kg/m^2 to g/m^2
    'wq'       : 1000,     # convert kg/kg m/s to g/kg m/s
    'zi'       : .001,     # convert m to km
    'zb'       : .001,     # convert m to km
    'Nc_0'     : 1e-6,     # convert m$^{-3}$, cm$^{-3}$, 
    'walltime' : 1.0/3600, # convert seconds to hours
    'z0'       : 1000      # convert m to mm
}

plot_labels = {
    'wtheta'   : r'$w_{\theta}$',
    'wq'       : '$w_q$',
    'we'       : '$w_e$',
    'walltime' : r'$\tau$',
    'zi'       : '$z_i$',
    'zb'       : '$z_b$',
    'iadv'     : 'adv.',
    'iadv_sv'  : 'rain adv.',
    'seed'     : 'seed',
    'l_sb'     : 'microphys.',
    'rwp'      : 'RWP',
    'lwp'      : 'LWP',
    'cfrac'    : '$C$',
    'prec'     : '$P_{srf}$',
    'z0'       : '$z_0$',
    'Nc_0'     : '$N_{c}$',
    'thls'     : r'$\theta_{s}$',
    'poissondigits' : '$d$',
    'cn'       : '$c_N$',      # Heus2010 cites Deardorf1980 for the subgrid formulation
    'Rigc'     : 'Ri$_c$',     # http://glossary.ametsoc.org/wiki/Bulk_richardson_number
    'Prandtl'  : 'Pr',
}


# adjust the order of discrete parameters 
# to avoid repeating integer parameters with small range
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
    
    # 3. Wrap Application
    #    - Define a new application, and the encoding/decoding elements it needs
    #    - Also requires a collation element - this will be responsible for aggregating the results

    # The encoder creates the input file to the model, from a template
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
        # work-around to prevent validation errors on integer quantities
        # needed when *all* quantities varied are discrete
    
    # 5. Get run parameters
    if args.sampler=='random':
        my_campaign.draw_samples(num_samples=args.num_samples, replicas=args.replicas)
    else:
        my_campaign.draw_samples(replicas=args.replicas)

    # 6. Create run input directories
    my_campaign.populate_runs_dir()

    print(my_campaign)

    # run pre-processing script for each run directory
    # used to copy input files that are common to each run
    prep_script=f"prep.sh {cwd+'/input'}"
    my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(prep_script))
    
    my_campaign.save_state(args.campaign)

################################################

if args.run:
    # 7. Run Application
    #    - dales is executed for each sample
    
    my_campaign = uq.Campaign(state_file=args.campaign, work_dir=args.workdir)


    if args.parallel:
        # run with gnu parallel, in parallel on the local machine
        pcmd = f"ls -d {my_campaign.campaign_dir}/runs/Run_* | parallel -j {args.parallel} 'cd {{}} ; {args.model} namoptions.001 > output.txt ;  cd .. '"
        print ('Parallel run command', pcmd)
        subprocess.call(pcmd, shell=True)
    elif args.fab: # run with FabSim
        fab.run_uq_ensemble(my_campaign.campaign_dir, script_name='dales', machine='eagle_vecma')
    else:
        # run sequentially
        my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(f"{args.model} namoptions.001 > output.txt"))
        
    my_campaign.save_state(args.campaign)



if args.fetch:    
    my_campaign = uq.Campaign(state_file=args.campaign, work_dir=args.workdir)
    if args.fab:
        print("Fetching results with FabSim:")
        fab.get_uq_samples(my_campaign.campaign_dir, machine='eagle_vecma')
    my_campaign.save_state(args.campaign)
                
if args.analyze:
    my_campaign = uq.Campaign(state_file=args.campaign, work_dir=args.workdir)
    my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(postproc, interpret='python3'))

    # 8. Collate output
    my_campaign.collate()
    # to re-run all collation, use my_campaign.recollate()
    
    data = my_campaign.get_collation_result()
    print(data)
    
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

    # perform analysis with EasyVVUQ
    my_campaign.apply_analysis(analysis)
    results = my_campaign.get_last_analysis()

    # from here on, it's reporting and plotting
    
    print(f"sampler: {args.sampler}, order: {args.order}")
    print('         --- Varied input parameters ---')
    print("  param    default      unit     distribution")
    for k in vary.keys():
        print("%8s %9.3g %9s  %s"%(k, params[k]['default'], unit.get(k, ''), str(vary[k])))
    print()

    print('         --- Output ---')
    var = list(vary.keys())

    latex = True # output tables in LaTeX format
    if latex:
        sep=' &'       # column separator
        end=r' \\'     # end of line
        percent=r'\%'  # percent sign
    else:
        sep = ' '
        end=''
        percent='%'
        
    if latex:
        print('\\begin{tabular}{lrr*{%d}{r}}'%len(var))
        print(r'\hline')

    #print("                                                  Sobol indices")
    print(f"       QoI  {sep}    mean {sep}std({percent})", end='')
    for v in var:
        if latex:
            v = plot_labels.get(v, v)
        print(sep, '%12s'%v, end='')
    print(end)
    if latex:
        print(r'\hline')
    
    for qoi in output_columns:
        if latex:
            q = plot_labels.get(qoi, qoi)
        else:
            q = qoi
            
        print("%12s"%q, end=sep)
        print("% 6.3g %9s%s% 6.1f"%(results['statistical_moments'][qoi]['mean'] * scale.get(qoi,1), unit[qoi], sep,
                       #% 6.3g%s             # results['statistical_moments'][qoi]['std'] * scale.get(qoi,1), sep, # st.dev.
                                               100*results['statistical_moments'][qoi]['std']/results['statistical_moments'][qoi]['mean']),
              end='')
        #print("%9s"%unit[qoi], end='')
        for v in var:
            print('%s %5.3f'%(sep, results['sobols_first'][qoi][v]), end='')
        print(end)

    if latex:
        print(r'\hline')
        print(r'\end{tabular}')
    print()
    
    # print multi-variable Sobol indices
    if args.sampler == 'sc':  # multi-var Sobol indices are not available for PCE
        for qoi in output_columns: 
            print(qoi, end=' ')
                  #results['statistical_moments'][qoi]['mean'][0], 
                  #results['statistical_moments'][qoi]['std'][0], end=' ')
            sobols = results['sobols'][qoi]
            for k in sobols:
                if len(k) > 1: # print only the combined indices
                    print(f"{k}: {sobols[k][0]:5.3f}", end=' ')
            print()

        
    # print(my_campaign.get_collation_result()) # a Pandas dataframe
    
    mplparams = {"figure.figsize" : [5.31, 4],  # figure size in inches
                 "figure.dpi"     :  200,      # figure dots per inch
                 "font.size"      :  6,        # this one acutally changes tick labels
                 'svg.fonttype'   : 'none',   # plot text as text - not paths or clones or other nonsense
                 'axes.linewidth' : .5, 
                 'xtick.major.width' : .5,
                 'ytick.major.width' : .5,
                 'font.family' : 'sans-serif',
                 'font.sans-serif' : ['PT Sans'],
    }
    plt.rcParams.update(mplparams)

    scalar_outputs = output_columns # [:-1]
    params = vary.keys()
    fig, ax = plt.subplots(nrows=len(scalar_outputs), ncols=len(params),
                           sharex='col', sharey='row', squeeze=False) # constrained_layout=True - sounds nice but didn't work
    # fig.set_tight_layout(True) - didn't work either.
    # layout adjustment at the end with subplots_adjust

    # manually specify tick locations for some parameters
    ticks = {
        'poissondigits' : [2,4,6,8,10,12],
        'iadv' : [0,1],
        'iadv_sv' : [0,1,2],
        'l_sb' : [0,1],
        'seed' : [],
    }
    # manually specify labels for some parameters
    ticklabels = {
        'iadv' : ['2nd', '5th'],
        'iadv_sv' : ['2nd', '5th', 'kappa'],
        'l_sb' : ['KK00', 'SB']
    }

    symbolsize = 1
    if len(params) == 2:
        symbolsize = 1.5 # larger symbols for the plot with fewer params

    # create grid of plots
    for i,param in enumerate(params):            # column
        for j,qoi in enumerate(scalar_outputs):  # row
            x = data[param] * scale.get(param,1)
            y = data[qoi]   * scale.get(qoi,1)
            xr = max(x) - min(x)

            # add spread in x, to show point cloud better
            x += (numpy.random.rand(len(x))-.5) * xr * .05            
            ax[j][i].plot(x, y, 'o', ms=symbolsize, mec='none', color='#ff8000')

            if param in ticks:
                ax[j][i].set_xticks(ticks[param])
                if param in ticklabels:
                    ax[j][i].set_xticklabels(ticklabels[param])
                
            # hide internal tick marks
            if i==0:
                ax[j][i].yaxis.set_ticks_position('left')
            else:
                ax[j][i].yaxis.set_ticks_position('none')
            if j==len(scalar_outputs)-1:
                ax[j][i].xaxis.set_ticks_position('bottom')
            else:
                ax[j][i].xaxis.set_ticks_position('none')

            
    # adding labels after all plots, hoping for better placement
    for i,param in enumerate(params):
        for j,qoi in enumerate(scalar_outputs):
            xu = unit.get(param,'')
            yu = unit.get(qoi,'')
            if xu: xu = f"({xu})"
            if yu: yu = f"({yu})"
            param_label = plot_labels.get(param, param)
            qoi_label = plot_labels.get(qoi, qoi)

            ax[j][i].set(xlabel=f"{param_label} {xu}")
            ax[j][i].set_ylabel(f"{qoi_label}", rotation=0)  #for y unit: \n{yu}
            ax[j][i].spines['top'].set_visible(False)
            ax[j][i].spines['right'].set_visible(False)
            
    for a in ax.flat:
        a.label_outer()
        a.ticklabel_format(axis='y', style='sci', scilimits=(-5,5), useOffset=None, useLocale=None, useMathText=True)            

    plt.subplots_adjust(left=.1, top=.99, bottom=.1, right=.99, wspace=.01, hspace=.01)
    
    if args.plot:
        print('Saving plot as', args.plot)
        plt.savefig(args.plot)
    #plt.show()
