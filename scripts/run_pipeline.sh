#!/bin/bash
TIMESTAMP=`date '+%Y-%m-%d-%H-%M-%S'`
echo $TIMESTAMP

# set up
cd /sw/molstar-volseg
git fetch origin
git reset --hard origin/master
git pull

/home/ubuntu/mambaforge/condabin/mamba env create --file environment_production.yaml \
|| /home/ubuntu/mambaforge/condabin/mamba env update --file environment_production.yaml --prune
source /home/ubuntu/mambaforge/bin/activate cellstar-volume-server-PRODUCTION

# run script
python preprocessor/cellstar_preprocessor/tools/deploy_db/download_and_build.py "$@" &> /sw/log_$TIMESTAMP.txt 