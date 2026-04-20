#!/usr/bin/env bash

set -e

cslc --arch=wse3 ./queue_flush_layout.csl --fabric-dims=9,3 \
--fabric-offsets=4,1 -o out --memcpy --channels 1
cs_python run.py --name out
