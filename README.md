# EasyVVUQ analysis scripts for the DALES model

This repository contains scripts and settings for
using [EasyVVUQ](https://github.com/UCL-CCS/EasyVVUQ/)
for uncertainty quantification of the atmospheric model
[DALES](https://github.com/dalesteam/dales).
The case setup is from the RICO study by van Zanten et al (see below).

## Requirements

* matplotlib
* numpy
* [EasyVVUQ](https://github.com/UCL-CCS/EasyVVUQ/) from the dev branch or the M24 release (August 2020)
* [FabSim3](https://github.com/djgroen/FabSim3) (optional)
* [DALES](https://github.com/dalesteam/dales), we used branch "to4.3", the pre-release of version 4.3

## Running

### Running locally

A DALES UQ experiment is done in three stages:

```
python easyvvuq_dales.py <other options> --prepare
# creates run directories for the model, one for each sample point in parameter space.

python easyvvuq_dales.py <other options> --run
# runs the DALES model for each directory created above

python easyvvuq_dales.py <other options> --analyze
# collects the results and preforms a UQ analysis,
# output is given with tables and plots.
```

The <other options> are used to define the experiment:

* `--workdir` base directory for EasyVVUQ to use for the model run directories. It creates a subdirectory here for each experiment.
* `--template` a template for the model parameter file, use one of the included files `namoptions*.template`.
* `--campaign` a json file name where EasyVVUQ stores the state of the campaign between the different steps.
* `--experiment` one of [physics_z0, poisson, test, choices, subgrid], used to select a set of parameters to vary (defined in the easyvvuq_dales.py script). Should match the template.
* `--model` path of the DALES executable


Adding the option `--parallel` <N> to the `--run` step, will use [GNU parallel](https://www.gnu.org/software/parallel/) to
run N model evaluations in parallel on the local machine.

### Running with FabSim3

See [this tutorial](https://github.com/wedeling/FabUQCampaign) for setting up FabSim3.
Use the same options as for a local run, with the addition of `--fab`,
and an additional `--fetch` step before `--analyze`.

```
python easyvvuq_dales.py <other options> --fab --prepare

python easyvvuq_dales.py <other options> --fab --run
# submits the jobs with FabSim on some remote machine

python easyvvuq_dales.py <other options> --fab --fetch
# fetches results with FabSim from the remote machine,
# run this after the jobs have completed.

python easyvvuq_dales.py <other options> --fab --analyze
```

Access details of the remote computer system, settings for the DALES installation there,
and run-time settings for the maximal wallclock time and number of MPI tasks for a job
need to be added to the FabSim configuration files, e.g. `deploy/machines_user.yml`.

## License

The scripts in this repository are made available under the terms of
the GNU GPL version 3, see the file COPYING for details. EasyVVUQ,
Fabsim3 and DALES have their own (open source) licenses.


## References

Formulation of the Dutch Atmospheric Large-Eddy Simulation (DALES) and overview of its applications,
T. Heus et al, [Geosci. Model Dev., 3, 415-444, 2010](https://doi.org/10.5194/gmd-3-415-2010)

Controls on precipitation and cloudiness in simulations of trade-wind cumulus as observed during RICO,
van Zanten et al, [Journal of Advances in Modeling Earth Systems 3. (2011)]({https://doi.org/10.1029/2011MS000056)

