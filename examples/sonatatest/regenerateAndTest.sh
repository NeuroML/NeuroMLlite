#!/bin/bash
set -ex

python SonataExample.py -sonata

python run_bmtk.py

./run_pynml.jnml.sh
