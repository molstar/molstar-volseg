#!/bin/bash

echo "Running deploy process"
screen -S "cellstar-build-db" -dm /sw/run_pipeline_build_db.sh "$@"
echo "Deploy command executed in the background..."
