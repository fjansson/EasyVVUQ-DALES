#!/bin/bash

# Poisson
# -------
# campaign dir /home/jansson/code/VECMA/rico/work/dales4oo2r225

#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-poisson.template --campaign=poissondigits-seedparam.json --experiment=poisson --prepare
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-poisson.template --campaign=poissondigits-seedparam.json --experiment=poisson --run
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-poisson.template --campaign=poissondigits-seedparam.json --experiment=poisson --fetch
python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-poisson.template --campaign=poissondigits-seedparam.json --experiment=poisson --analyze --plot poisson.pdf

# Choices
# -------
# campaign dir /home/jansson/code/VECMA/rico/work/dalessp3gkchu
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-choices.template --campaign=choices.json --experiment=choices --prepare
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-choices.template --campaign=choices.json --experiment=choices --run
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-choices.template --campaign=choices.json --experiment=choices --fetch
python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-choices.template --campaign=choices.json --experiment=choices --analyze --plot choices.pdf

# Physics  v2 with smaller z0 range
# -------
#campaign dir /home/jansson/code/VECMA/rico/work/dales0dzdxjo_

#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0_v2.json --experiment=physics_z0 --prepare
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0_v2.json --experiment=physics_z0 --run
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0_v2.json --experiment=physics_z0 --fetch
python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0_v2.json --experiment=physics_z0 --analyze --plot physics.pdf


############ older runs

# subgrid
# -------
#campaign dir /home/jansson/code/VECMA/rico/work/daleslwyj23_l
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions.template --campaign=subgrid.json --experiment=subgrid --prepare
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions.template --campaign=subgrid.json --experiment=subgrid --run
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions.template --campaign=subgrid.json --experiment=subgrid --fetch
python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions.template --campaign=subgrid.json --experiment=subgrid --analyze --plot subgrid.pdf

# physics_z0   - v1 with wide z0 range 1e-4 ... 1e-1
# ----------
# campaign dir /home/jansson/code/VECMA/rico/work/dalesqu0dgu1a
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0.json --experiment=physics_z0 --prepare
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0.json --experiment=physics_z0 --run
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0.json --experiment=physics_z0 --fetch
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0.json --experiment=physics_z0 --analyze --plot physics-large-z0.svg


