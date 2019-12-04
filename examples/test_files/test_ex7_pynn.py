import os
import sys
from neuromllite.NetworkGenerator import check_to_generate_or_run

os.chdir("..")
sys.path.append(".")

print('Running PyNN Ex7 test script with %s'%sys.argv)

if 'nest' in sys.argv:
    sys.argv.append('-pynnnest')
if 'neuron' in sys.argv:
    sys.argv.append('-pynnnrn')
if 'brian' in sys.argv:
    sys.argv.append('-pynnbrian')

from Example7 import generate

sim, net = generate()

check_to_generate_or_run(sys.argv, sim)