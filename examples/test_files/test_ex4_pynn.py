import os, sys

os.chdir("..")
sys.path.append(".")

if 'nest' in sys.argv:
    sys.argv.append('-pynnnest')
if 'neuron' in sys.argv:
    sys.argv.append('-pynnnrn')
if 'brian' in sys.argv:
    sys.argv.append('-pynnbrian')

import Example4
