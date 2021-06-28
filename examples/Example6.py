from neuromllite import Network, Cell, Population, Simulation, Synapse
from neuromllite import RectangularRegion, RandomLayout
from neuromllite import Projection, RandomConnectivity, OneToOneConnector

import sys

def generate(ref='Example6_PyNN', add_inputs=True):

    ################################################################################
    ###   Build new network

    net = Network(id=ref, notes = 'Another network for PyNN - work in progress...')
    
    net.parameters = { 'N_scaling': 0.005,
                       'layer_height': 400,
                       'width': 100,
                       'depth': 100,
                       'input_weight': 0.1}

    cell = Cell(id='CorticalCell', pynn_cell='IF_curr_exp')
    cell.parameters = {
        'cm'        : 0.25,  # nF
        'i_offset'  : 0.0,   # nA
        'tau_m'     : 10.0,  # ms
        'tau_refrac': 2.0,   # ms
        'v_reset'   : -65.0,  # mV
        'v_rest'    : -65.0,  # mV
        'v_thresh'  : -50.0  # mV
    }
    net.cells.append(cell)

    if add_inputs:
        input_cell = Cell(id='InputCell', pynn_cell='SpikeSourcePoisson')
        input_cell.parameters = {
            'start':    0,
            'duration': 10000000000,
             'rate':      150
        }
        net.cells.append(input_cell)

    e_syn = Synapse(id='ampa', 
                    pynn_receptor_type='excitatory', 
                    pynn_synapse_type='curr_exp',
                    parameters={'tau_syn':0.5})
    net.synapses.append(e_syn)
    i_syn = Synapse(id='gaba', 
                    pynn_receptor_type='inhibitory', 
                    pynn_synapse_type='curr_exp', 
                    parameters={'tau_syn':0.5})
    net.synapses.append(i_syn)

    N_full = {
      'L23': {'E': 20683, 'I': 5834},
      'L4' : {'E': 21915, 'I': 5479},
      'L5' : {'E': 4850, 'I': 1065},
      'L6' : {'E': 14395, 'I': 2948}
    }

    scale = 0.1

    pops = []
    input_pops = []
    pop_dict = {}

    layers = ['L23']
    layers = ['L23','L4','L5','L6']

    for l in layers:

        i = 3-layers.index(l)
        r = RectangularRegion(id=l, 
                              x=0,
                              y=i*net.parameters['layer_height'],
                              z=0,
                              width=net.parameters['width'],
                              height=net.parameters['layer_height'],
                              depth=net.parameters['depth'])
        net.regions.append(r)                     

        for t in ['E','I']:

            try:
                import opencortex.utils.color as occ
                if l == 'L23':
                    if t=='E': color = occ.L23_PRINCIPAL_CELL
                    if t=='I': color = occ.L23_INTERNEURON
                if l == 'L4':
                    if t=='E': color = occ.L4_PRINCIPAL_CELL
                    if t=='I': color = occ.L4_INTERNEURON
                if l == 'L5':
                    if t=='E': color = occ.L5_PRINCIPAL_CELL
                    if t=='I': color = occ.L5_INTERNEURON
                if l == 'L6':
                    if t=='E': color = occ.L6_PRINCIPAL_CELL
                    if t=='I': color = occ.L6_INTERNEURON

            except:
                color = '.8 0 0' if t=='E' else '0 0 1'

            pop_id = '%s_%s'%(l,t)
            pops.append(pop_id)
            ref = 'l%s%s'%(l[1:],t.lower())
            exec(ref + " = Population(id=pop_id, size='int(%s*N_scaling)'%N_full[l][t], component=cell.id, properties={'color':color, 'type':t})")
            exec("%s.random_layout = RandomLayout(region = r.id)"%ref)
            exec("net.populations.append(%s)"%ref)
            exec("pop_dict['%s'] = %s"%(pop_id,ref))
            

            if add_inputs:
                color = '.8 .8 .8'
                input_id = '%s_%s_input'%(l,t)
                input_pops.append(input_id)
                input_ref = 'l%s%s_i'%(l[1:],t.lower())
                exec(input_ref + " = Population(id=input_id, size='int(%s*N_scaling)'%N_full[l][t], component=input_cell.id, properties={'color':color})")
                exec("%s.random_layout = RandomLayout(region = r.id)"%input_ref)
                exec("net.populations.append(%s)"%input_ref)

        #l23i = Population(id='L23_I', size=int(100*scale), component=cell.id, properties={'color':})
        #l23ei = Population(id='L23_E_input', size=int(100*scale), component=input_cell.id)
        #l23ii = Population(id='L23_I_input', size=int(100*scale), component=input_cell.id)

    #net.populations.append(l23e)
    #net.populations.append(l23ei)
    #net.populations.append(l23i)
    #net.populations.append(l23ii)


    conn_probs = [[0.1009,  0.1689, 0.0437, 0.0818, 0.0323, 0.,     0.0076, 0.    ],
                 [0.1346,   0.1371, 0.0316, 0.0515, 0.0755, 0.,     0.0042, 0.    ],
                 [0.0077,   0.0059, 0.0497, 0.135,  0.0067, 0.0003, 0.0453, 0.    ],
                 [0.0691,   0.0029, 0.0794, 0.1597, 0.0033, 0.,     0.1057, 0.    ],
                 [0.1004,   0.0622, 0.0505, 0.0057, 0.0831, 0.3726, 0.0204, 0.    ],
                 [0.0548,   0.0269, 0.0257, 0.0022, 0.06,   0.3158, 0.0086, 0.    ],
                 [0.0156,   0.0066, 0.0211, 0.0166, 0.0572, 0.0197, 0.0396, 0.2252],
                 [0.0364,   0.001,  0.0034, 0.0005, 0.0277, 0.008,  0.0658, 0.1443]]

    if add_inputs:
        for p in pops:
            proj = Projection(id='proj_input_%s'%p,
                            presynaptic='%s_input'%p, 
                            postsynaptic=p,
                            synapse=e_syn.id,
                            delay=2,
                            weight='input_weight')
            proj.one_to_one_connector=OneToOneConnector()
            net.projections.append(proj)

    for pre_i in range(len(pops)):
        for post_i in range(len(pops)):
            pre = pops[pre_i]
            post = pops[post_i]
            prob = conn_probs[post_i][pre_i]   #######   TODO: check!!!!
            weight = 1
            syn = e_syn
            if prob>0:
                if 'I'in pre:
                    weight = -1
                    syn = i_syn
                proj = Projection(id='proj_%s_%s'%(pre,post),
                                presynaptic=pre, 
                                postsynaptic=post,
                                synapse=syn.id,
                                delay=1,
                                weight=weight)
                proj.random_connectivity=RandomConnectivity(probability=prob)
                net.projections.append(proj)


    print(net.to_json())
    new_file = net.to_json_file('%s.json'%net.id)

    ################################################################################
    ###   Build Simulation object & save as JSON

    recordTraces={}
    recordSpikes={}
    
    from neuromllite.utils import evaluate
    for p in pops:
        forecast_size = evaluate(pop_dict[p].size, net.parameters)
        recordTraces[p]=list(range(min(2,forecast_size)))
        recordSpikes[p]='*'
    for ip in input_pops:
        recordSpikes[ip]='*'
        
    sim = Simulation(id='Sim%s'%net.id,
                     network=new_file,
                     duration='100',
                     dt='0.025',
                     seed=1234,
                     recordTraces=recordTraces,
                     recordSpikes=recordSpikes)

    sim.to_json_file()

    return sim, net


if __name__ == "__main__":
    
    
    if '-noinputs' in sys.argv:
        sim, net = generate('Example6_PyNN_noinputs', False)
    else:
        sim, net = generate('Example6_PyNN', True)
    
        

    ################################################################################
    ###   Run in some simulators

    from neuromllite.NetworkGenerator import check_to_generate_or_run

    check_to_generate_or_run(sys.argv, sim)


