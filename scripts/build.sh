#!/bin/bash

echo "Running deploy process"
screen -ls | awk -vFS='\t|[.]' '/cellstar-download-and-build-db/ {system("screen -S "$2" -X quit")}'
screen -S "cellstar-download-and-build-db" -dm /sw/run_pipeline.sh "$@"
echo "Deploy command executed in the background..."