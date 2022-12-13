#!/bin/bash

echo "Running deploy process"
screen -S "cellstar-api" -dm /sw/run_api_pipeline.sh "$@"
echo "Deploy command executed in the background..."
