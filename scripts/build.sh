#!/bin/bash

echo "Running deploy process"
screen -S "cellstar" -dm /sw/run_pipeline.sh "$@"
echo "Deploy command executed in the background..."
