#!/bin/bash

# link input files from $1 into the current directory

# echo prep.sh: ln -s $1/* ./
#ln -s $1/* ./

#copy files instead of linking, to work also with fabsim
cp $1/* ./


# sed -i namoptions.001 -e "s/BOOLEAN1/.true./;s/BOOLEAN0/.false./"
