#!/bin/bash
TIMESTAMP=`date '+%Y-%m-%d-%H-%M-%S'`
echo $TIMESTAMP

cd /sw/cellstar-volume-server
git reset --hard origin/master
git pull

source /sw/mambaforge/bin/activate cellstar-volume-server
mamba env update --file environment.yaml --prune

pip install -e .

python preprocessor/src/tools/deploy_db/deploy_api.py "$@" &> /sw/log_api_$TIMESTAMP.txt 

