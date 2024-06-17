#!/bin/bash

echo "Running deploy process"
screen -ls | awk -vFS='\t|[.]' '/cellstar-api/ {system("screen -S "$2" -X quit")}'
screen -S "cellstar-api" -dm /sw/run_api_pipeline.sh "$@"
echo "Deploy command executed in the background..."