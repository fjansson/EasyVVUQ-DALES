#!/bin/bash

# Poisson
# -------
# campaign dir  /home/jansson/code/VECMA/rico/work/dales4oo2r225

#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-poisson.template --campaign=poissondigits-seedparam.json --experiment=poisson --fetch

#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-poisson.template --campaign=poissondigits-seedparam.json --experiment=poisson --analyze --plot poisson.svg

# choices
# -------
# campaign dir /home/jansson/code/VECMA/rico/work/dalessp3gkchu/
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-choices.template --campaign=choices.json --experiment=choices --fetch

#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-choices.template --campaign=choices.json --experiment=choices --analyze --plot choices.svg

# physics  v2 with smaller z0 range
# -------
# campaign_dir=/home/jansson/code/VECMA/rico/work/dales0dzdxjo_
# python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0_v2.json --experiment=physics_z0 --fetch

#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0_v2.json --experiment=physics_z0 --analyze --plot physics.svg


# subgrid
# -------
# campaign_dir = /home/jansson/code/VECMA/rico/work/daleslwyj23_l
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions.template --campaign=subgrid.json --experiment=subgrid --fetch

#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions.template --campaign=subgrid.json --experiment=subgrid --analyze --plot subgrid.svg







############ older runs

# physics_z0   - v1 with wide z0 range 1e-4 ... 1e-1
# ----------
# campaign dir  /home/jansson/code/VECMA/rico/work/dalesqu0dgu1a
#python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0.json --experiment=physics_z0 --fetch

python easyvvuq_dales.py --workdir=/home/jansson/code/VECMA/rico/work --fab --template=namoptions-z0.template --campaign=physics_z0.json --experiment=physics_z0 --analyze --plot physics-large-z0.svg


