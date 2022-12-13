#!/bin/bash

source activate cellstar-volume-server
uvicorn main:app --ssl-keyfile /sw/cert/serverkey.pem --ssl-certfile /sw/cert/cert.pem --ssl-keyfile-password cellstar
