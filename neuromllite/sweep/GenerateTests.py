from neuromllite import *
from neuromllite.NetworkGenerator import *
from neuromllite.utils import create_new_model
import sys




if __name__ == "__main__":
    
    hhcell = Cell(id='hhcell', 
                  neuroml2_source_file='../../examples/test_files/hhcell.cell.nml')

    iclamp = InputSource(id='iclamp_0', 
                               neuroml2_input='PulseGenerator', 
                               parameters={'amplitude':'stim_amp', 'delay':'stim_del', 'duration':'200ms'})
                               
    parameters = {'stim_amp':'100pA', 'stim_del':'50ms'}
    
    sim, network = create_new_model('HHTest',
                     300,
                     parameters = parameters,
                     cell_for_default_population=hhcell,
                     input_for_default_population=iclamp)
    
    '''
    pynncell = Cell(id='pynncell', 
                    pynn_cell='IF_cond_alpha',
                    parameters = { "tau_refrac":5, "i_offset":0 })

    
    sim, network = create_new_model('PyNNTest',
                     300,
                     parameters = parameters,
                     cell_for_default_population=pynncell,
                     input_for_default_population=iclamp)'''
                     
                     
    check_to_generate_or_run(sys.argv, sim)