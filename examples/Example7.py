from neuromllite import Network, Cell, InputSource, Population, Synapse
from neuromllite import Projection, RandomConnectivity, OneToOneConnector, Input, Simulation

from neuromllite.NetworkGenerator import check_to_generate_or_run
from neuromllite.sweep.ParameterSweep import *

import sys


def generate():
    ################################################################################
    ###   Build new network

    net = Network(id='Example7_Brunel2000')
    net.notes = 'Example 7: based on network of Brunel 2000'

    net.parameters = { 'g':       4, 
                       'eta':     1, 
                       'order':   5,
                       'epsilon': 0.1,
                       'J':       0.1,
                       'delay':   1.5,
                       'tauMem':  20.0,
                       'tauSyn':  0.1,
                       'tauRef':  2.0,
                       'U0':      0.0,
                       'theta':   20.0}

    cell = Cell(id='ifcell', pynn_cell='IF_curr_alpha')


    cell.parameters = { 'tau_m':       'tauMem', 
                        'tau_refrac':  'tauRef',
                        'v_rest':      'U0',
                        'v_reset':     'U0',
                        'v_thresh':    'theta',
                        'cm':          0.001,
                        "i_offset":    0}

    #cell = Cell(id='hhcell', neuroml2_source_file='test_files/hhcell.cell.nml')
    net.cells.append(cell)

    expoisson = Cell(id='expoisson', pynn_cell='SpikeSourcePoisson')
    expoisson.parameters = { 'rate':       '1000 * (eta*theta/(J*4*order*epsilon*tauMem)) * (4*order*epsilon)',
                             'start':      0,
                             'duration':   1e9}
    net.cells.append(expoisson)


    '''
    input_source = InputSource(id='iclamp0', 
                               pynn_input='DCSource', 
                               parameters={'amplitude':0.002, 'start':100., 'stop':900.})

    input_source = InputSource(id='poissonFiringSyn', 
                               neuroml2_input='poissonFiringSynapse',
                               parameters={'average_rate':"eta", 'synapse':"ampa", 'spike_target':"./ampa"})



    net.input_sources.append(input_source)'''

    pE = Population(id='Epop', size='4*order', component=cell.id, properties={'color':'1 0 0'})
    pEpoisson = Population(id='Einput', size='4*order', component=expoisson.id, properties={'color':'.5 0 0'})
    pI = Population(id='Ipop', size='1*order', component=cell.id, properties={'color':'0 0 1'})

    net.populations.append(pE)
    net.populations.append(pEpoisson)
    net.populations.append(pI)


    net.synapses.append(Synapse(id='ampa', 
                                pynn_receptor_type='excitatory', 
                                pynn_synapse_type='curr_alpha', 
                                parameters={'tau_syn':0.1}))
    net.synapses.append(Synapse(id='gaba', 
                                pynn_receptor_type='inhibitory', 
                                pynn_synapse_type='curr_alpha', 
                                parameters={'tau_syn':0.1}))


    net.projections.append(Projection(id='projEinput',
                                      presynaptic=pEpoisson.id, 
                                      postsynaptic=pE.id,
                                      synapse='ampa',
                                      delay=2,
                                      weight=0.02,
                                      one_to_one_connector=OneToOneConnector()))
    '''           
    net.projections.append(Projection(id='projEE',
                                      presynaptic=pE.id, 
                                      postsynaptic=pE.id,
                                      synapse='ampa',
                                      delay=2,
                                      weight=0.002,
                                      random_connectivity=RandomConnectivity(probability=.5)))'''

    net.projections.append(Projection(id='projEI',
                                      presynaptic=pE.id, 
                                      postsynaptic=pI.id,
                                      synapse='ampa',
                                      delay=2,
                                      weight=0.02,
                                      random_connectivity=RandomConnectivity(probability=.5)))
    '''
    net.projections.append(Projection(id='projIE',
                                      presynaptic=pI.id, 
                                      postsynaptic=pE.id,
                                      synapse='gaba',
                                      delay=2,
                                      weight=0.02,
                                      random_connectivity=RandomConnectivity(probability=.5)))

    net.inputs.append(Input(id='stim',
                            input_source=input_source.id,
                            population=pE.id,
                            percentage=50))'''

    #print(net)
    #print(net.to_json())
    new_file = net.to_json_file('%s.json'%net.id)


    ################################################################################
    ###   Build Simulation object & save as JSON

    sim = Simulation(id='SimExample7',
                     network=new_file,
                     duration='1000',
                     dt='0.025',
                     seed= 123,
                     recordTraces={pE.id:'*',pI.id:'*'},
                     recordSpikes={'all':'*'})

    sim.to_json_file()
    
    return sim, net



if __name__ == "__main__":

    if '-sweep' in sys.argv:
        
        sim, net = generate()
        
        fixed = {'dt':0.001, 'order':1}
 
        #
        vary = {'eta':[0.5,1,1.5,2]}
        #vary = {'eta':[1,2]}
        #vary = {'eta':[1]}
        #vary = {'eta':[i/1000. for i in xrange(0,200,20)]}
        #vary = {'stim_amp':['1.5pA']}
        
        vary['seed'] = [1,2,3,4,5]

        simulator = 'jNeuroML'
        simulator = 'jNeuroML_NEURON'
        simulator = 'jNeuroML_NetPyNE'
        simulator = 'PyNN_NEST'
        simulator = 'jNeuroML'

        nmllr = NeuroMLliteRunner('SimExample7.json',
                                  simulator=simulator)

        ps = ParameterSweep(nmllr, 
                            vary, 
                            fixed,
                            num_parallel_runs=16,
                            plot_all=True, 
                            heatmap_all=False,
                            show_plot_already=False,
                            peak_threshold=0)

        report = ps.run()
        ps.print_report()

        #  ps.plotLines('weightInput','average_last_1percent',save_figure_to='average_last_1percent.png')
        #ps.plotLines('weightInput','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
        #ps.plotLines('eta','Einput[0]/spike:mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
        ps.plotLines('eta','Einput[0]/spike:mean_spike_frequency',second_param='seed',save_figure_to='mean_spike_frequency.png')

        import matplotlib.pyplot as plt

        plt.show()
    
    else:

        sim, net = generate()

        ################################################################################
        ###   Run in some simulators

        import sys

        check_to_generate_or_run(sys.argv, sim)

