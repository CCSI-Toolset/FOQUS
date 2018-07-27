#!/bin/bash
# Automated Testing Script for Foqus
conda env create -f foqus_env.yml
source activate foqus_env
python setup.py develop
python foqus.py -s "examples\Smoke Tests\fs_smoke_test.py"
source deactivate
conda remove --name foqus_env --all