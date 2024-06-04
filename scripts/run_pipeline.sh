#!/bin/bash
TIMESTAMP=`date '+%Y-%m-%d-%H-%M-%S'`
echo $TIMESTAMP

cd /sw/molstar-volseg
git reset --hard origin/master
git pull

source /sw/mambaforge/bin/activate cellstar-volume-server
mamba env update --file environment.yaml --prune

# pip install -e .

python preprocessor/cellstar_preprocessor/tools/deploy_db/build.py > "$@" &> /sw/log_$TIMESTAMP.txt 
# python preprocessor/src/tools/deploy_db/build_and_deploy.py "$@" &> /sw/log_$TIMESTAMP.txt 

