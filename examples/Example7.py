from neuromllite import Network, Cell, Population, Synapse, RectangularRegion, RandomLayout 
from neuromllite import Projection, RandomConnectivity, OneToOneConnector, Simulation

from neuromllite.NetworkGenerator import check_to_generate_or_run
from neuromllite.sweep.ParameterSweep import *

import sys


def generate():
    
    dt = 0.025
    simtime = 1000
    
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

    poisson_input = Cell(id='poisson_input', pynn_cell='SpikeSourcePoisson')
    poisson_input.parameters = { 'rate':       '1000 * (eta*theta/(J*4*order*epsilon*tauMem)) * (4*order*epsilon)',
                             'start':      0,
                             'duration':   1e9}
    net.cells.append(poisson_input)

    r1 = RectangularRegion(id='region1', x=0,y=0,z=0,width=1000,height=100,depth=1000)
    net.regions.append(r1)

    pE = Population(id='Epop', 
                    size='4*order', 
                    component=cell.id, 
                    properties={'color':'.9 0 0', 'radius':5},
                    random_layout = RandomLayout(region=r1.id))
    pEpoisson = Population(id='expoisson', 
                           size='4*order', 
                           component=poisson_input.id, 
                           properties={'color':'0.9 0.7 0.7', 'radius':3},
                           random_layout = RandomLayout(region=r1.id))
    pI = Population(id='Ipop', 
                    size='1*order', 
                    component=cell.id, 
                    properties={'color':'0 0 .9', 'radius':5},
                    random_layout = RandomLayout(region=r1.id))
    pIpoisson = Population(id='inpoisson', 
                           size='1*order', 
                           component=poisson_input.id, 
                           properties={'color':'0.7 0.7 0.9', 'radius':3},
                           random_layout = RandomLayout(region=r1.id))

    net.populations.append(pE)
    net.populations.append(pEpoisson)
    net.populations.append(pI)
    net.populations.append(pIpoisson)


    net.synapses.append(Synapse(id='ampa', 
                                pynn_receptor_type='excitatory', 
                                pynn_synapse_type='curr_alpha', 
                                parameters={'tau_syn':0.1}))
                                
    net.synapses.append(Synapse(id='gaba', 
                                pynn_receptor_type='inhibitory', 
                                pynn_synapse_type='curr_alpha', 
                                parameters={'tau_syn':0.1}))

    delay_ext = dt
    
    net.projections.append(Projection(id='projEinput',
                                      presynaptic=pEpoisson.id, 
                                      postsynaptic=pE.id,
                                      synapse='ampa',
                                      delay=delay_ext,
                                      weight=0.000413635066326,
                                      one_to_one_connector=OneToOneConnector()))
    
    net.projections.append(Projection(id='projIinput',
                                      presynaptic=pIpoisson.id, 
                                      postsynaptic=pI.id,
                                      synapse='ampa',
                                      delay=delay_ext,
                                      weight=0.000413635066326,
                                      one_to_one_connector=OneToOneConnector()))
                                      
           
    net.projections.append(Projection(id='projEE',
                                      presynaptic=pE.id, 
                                      postsynaptic=pE.id,
                                      synapse='ampa',
                                      delay='delay',
                                      weight=0.000413635066326,
                                      random_connectivity=RandomConnectivity(probability='epsilon')))

    net.projections.append(Projection(id='projEI',
                                      presynaptic=pE.id, 
                                      postsynaptic=pI.id,
                                      synapse='ampa',
                                      delay='delay',
                                      weight=0.000413635066326,
                                      random_connectivity=RandomConnectivity(probability='epsilon')))
    
    net.projections.append(Projection(id='projIE',
                                      presynaptic=pI.id, 
                                      postsynaptic=pE.id,
                                      synapse='gaba',
                                      delay='delay',
                                      weight=-0.001654540265306,
                                      random_connectivity=RandomConnectivity(probability='epsilon')))
                                      
    net.projections.append(Projection(id='projII',
                                      presynaptic=pI.id, 
                                      postsynaptic=pI.id,
                                      synapse='gaba',
                                      delay='delay',
                                      weight=-0.001654540265306,
                                      random_connectivity=RandomConnectivity(probability='epsilon')))

    #print(net)
    #print(net.to_json())
    new_file = net.to_json_file('%s.json'%net.id)


    ################################################################################
    ###   Build Simulation object & save as JSON

    sim = Simulation(id='SimExample7',
                     network=new_file,
                     duration=simtime,
                     dt=dt,
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
        vary = {'eta':[0.5,1,1.5,2,5,8,10]}
        #vary = {'eta':[1,2]}
        #vary = {'eta':[1]}
        #vary = {'eta':[i/1000. for i in xrange(0,200,20)]}
        #vary = {'stim_amp':['1.5pA']}
        
        vary['seed'] = [i for i in range(10)]

        simulator = 'jNeuroML'
        simulator = 'PyNN_NEST'
        simulator = 'jNeuroML'
        simulator = 'jNeuroML_NetPyNE'
        simulator = 'jNeuroML_NEURON'

        nmllr = NeuroMLliteRunner('SimExample7.json',
                                  simulator=simulator)

        ps = ParameterSweep(nmllr, 
                            vary, 
                            fixed,
                            num_parallel_runs=16,
                            plot_all=False, 
                            heatmap_all=False,
                            show_plot_already=False,
                            peak_threshold=0)

        report = ps.run()
        ps.print_report()

        #  ps.plotLines('weightInput','average_last_1percent',save_figure_to='average_last_1percent.png')
        #ps.plotLines('weightInput','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
        #ps.plotLines('eta','Einput[0]/spike:mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
        ps.plotLines('eta','Einput[0]/spike:mean_spike_frequency',second_param='seed',save_figure_to='mean_spike_frequency_ein.png')
        ps.plotLines('eta','Epop[0]/spike:mean_spike_frequency',second_param='seed',save_figure_to='mean_spike_frequency_e.png')
        ps.plotLines('eta','Ipop[0]/spike:mean_spike_frequency',second_param='seed',save_figure_to='mean_spike_frequency_i.png')

        import matplotlib.pyplot as plt

        plt.show()
    
    else:

        sim, net = generate()

        ################################################################################
        ###   Run in some simulators

        import sys

        check_to_generate_or_run(sys.argv, sim)

