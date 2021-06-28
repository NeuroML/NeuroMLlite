import os
import sys
from neuromllite.NetworkGenerator import check_to_generate_or_run

os.chdir("..")
sys.path.append(".")

sys.argv.append('-jnml')

from Example7 import generate

sim, net = generate()

check_to_generate_or_run(sys.argv, sim)