#!/bin/bash

echo "Running frontend deploy process"
screen -S "cellstar_frontend" -dm /sw/run_frontend_pipeline.sh "$@"
echo "Deploy command executed in the background..."
