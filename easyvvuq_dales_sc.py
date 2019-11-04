import os
import easyvvuq as uq
import chaospy as cp

# Trying DALES with EasyVVUQ
# based on EasyVVUQ gauss tutorial
# Fredrik Jansson Nov. 2019

# 0. Setup some variables describing app to be run
#
#    gauss.py is in current directory and takes one input file
#    and writes to 'output.csv'.
dales_exe = "~/code/official-dales/build/src/dales4"
cwd = os.getcwd()
input_filename = 'namoptions.001'
cmd = f"{dales_exe} {input_filename}"
out_file = "results.csv"

# Template input to substitute values into for each run
template = f"{cwd}/namoptions.template"

# 1. Create campaign
my_campaign = uq.Campaign(name='dales', work_dir="/tmp")
# all run directories created under workdir

# 2. Parameter space definition
params = {
    "Nc_0": {
        "type": "float",
        "min": 0.1e6,
        "max": 1000e6,
        "default": 70e6
    },
    "cf": {  # cf subgrid filter constant
        "type": "float",
        "min": 1.0,     # min, max are just guesses 
        "max": 4.0,  
        "default": 2.5
    },
    "Prandtl": {  # Prandtl number, subgrid.
        "type": "float",
        "min": 0.1,     # min, max are just guesses 
        "max": 1.0,  
        "default": 1.0/3}
}

# 3. Wrap Application
#    - Define a new application (we'll call it 'gauss'), and the encoding/decoding elements it needs
#    - Also requires a collation element - his will be responsible for aggregating the results
encoder = uq.encoders.GenericEncoder(template_fname=template,
                                     target_filename=input_filename)

output_columns = ['cfrac', 'lwp', 'zb', 'prec']

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

# 4. Specify Sampler
#    
vary = {
    "Nc_0"    : cp.Uniform(50e6, 100e6),
    "cf"      : cp.Uniform(2,3)}
#    "Prandtl" : cp.Uniform(0.2, 0.4), 
#}

my_sampler = uq.sampling.SCSampler(vary=vary, polynomial_order=2,
                                   quadrature_rule="G")

my_campaign.set_sampler(my_sampler)

# 5. Get run parameters
my_campaign.draw_samples()

# 6. Create run input directories
my_campaign.populate_runs_dir()

print(my_campaign)

# 7. Run Application
#    - dales is executed for each sample

#link='/usr/bin/ln -s ../../../input/* ./' #make links to input data in each run directory
# doesn't work - used with an absolute path.

link=f"link.sh {cwd+'/input'}"
postproc="postproc.py"
my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(link))
my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(cmd))
my_campaign.apply_for_each_run_dir(uq.actions.ExecuteLocal(postproc, interpret='python3'))

# 8. Collate output
my_campaign.collate()

# 9. Run Analysis
analysis = uq.analysis.SCAnalysis(sampler=my_sampler, qoi_cols=output_columns)

my_campaign.apply_analysis(analysis)

results = my_campaign.get_last_analysis()

###################################
# Plot the moments and SC samples #
###################################

mu_lwp = results['statistical_moments']['lwp']['mean']
std_lwp = results['statistical_moments']['lwp']['std']

for qoi in output_columns:
    print(qoi, results['statistical_moments'][qoi]['mean'], 
               results['statistical_moments'][qoi]['std'],
               'sobols:', results['sobols'][qoi],
               'sobols_first:', results['sobols_first'][qoi])



