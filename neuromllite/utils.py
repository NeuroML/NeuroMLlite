from neuromllite import *
import sys
import json

from neuromllite.BaseTypes import print_v, print_
    
    
def load_json(filename):
    """
    Load a generic JSON file
    """

    with open(filename, 'r') as f:
        
        data = json.load(f, object_hook=ascii_encode_dict)
        
    return data

    
def load_network_json(filename):
    """
    Load a NeuroMLlite network JSON file
    """
    
    data = load_json(filename)
        
    print_v("Loaded network specification from %s"%filename)
    
    net = Network()
    net = _parse_element(data, net)
    
    return net
    
    
def load_simulation_json(filename):
    """
    Load a NeuroMLlite simulation JSON file
    """

    with open(filename, 'r') as f:
        
        data = json.load(f, object_hook=ascii_encode_dict)
        
        
    print_v("Loaded simulation specification from %s"%filename)
    
    sim = Simulation()
    sim = _parse_element(data, sim)
    
    return sim


def save_to_json_file(info, filename, indent=4):

    strj = json.dumps(info, indent=indent)    
    with open(filename, 'w') as fp:
        fp.write(strj)

    
def ascii_encode_dict(data):
    ascii_encode = lambda x: x.encode('ascii') if (sys.version_info[0]==2 and isinstance(x, unicode)) else x
    return dict(map(ascii_encode, pair) for pair in data.items()) 
    
    
def _parse_element(json, to_build):

    for k in json.keys():
        to_build.id = k
        to_build = _parse_attributes(json[k], to_build)
               
    return to_build 
            
            
def _parse_attributes(json, to_build):
            
    for g in json:
        value = json[g]
        
        #print("  Setting %s=%s (%s) in %s"%(g, value, type(value), to_build))
        if type(to_build)==dict:
            to_build[g]=value
        elif type(value)==str or type(value)==int or type(value)==float:
            to_build.__setattr__(g, value)
        elif type(value)==list:
            type_to_use = to_build.allowed_children[g][1]

            for l in value:
                ff = type_to_use()
                ff = _parse_element(l, ff)
                exec('to_build.%s.append(ff)'%g)
        else:
            type_to_use = to_build.allowed_fields[g][1]
            ff = type_to_use()
            ff = _parse_attributes(value, ff)
            exec('to_build.%s = ff'%g)
                
        
    return to_build
    

def evaluate(expr, parameters={}):
    """
    Evaluate a general string like expression (e.g. "2 * weight") using a dict
    of parameters (e.g. {'weight':10}). Returns floats, ints, etc. if that's what's 
    given in expr
    """
    
    verbose = False
    #verbose = True
    print_(' > Evaluating: [%s] which is a %s vs parameters: %s...'%(expr,type(expr),parameters.keys() if parameters else None),verbose)
    try:
        if expr in parameters:
            expr = parameters[expr]  # replace with the value in parameters & check whether it's float/int...
        
        if type(expr)==str:
            try:
                expr = int(expr)
            except:
                pass
            try:
                expr = float(expr)
            except:
                pass
            
        if int(expr)==expr:
            print_('Returning int: %s'%int(expr),verbose)
            return int(expr)
        else: # will have failed if not number
            print_('Returning float: %s'%expr,verbose)
            return float(expr)
    except:
        try:
            print_('Trying eval with Python...',verbose)
            v = eval(expr, parameters)
            print_('Evaluated with Python: %s = %s (%s)'%(expr,v, type(v)),verbose)
            if int(v)==v:
                print_('Returning int: %s'%int(v),verbose)
                return int(v)
            return v
        except Exception as e:
            print_('Returning without altering: %s (error: %s)'%(expr,e),verbose)
            return expr
        
        
def get_pops_vs_cell_indices(recordSpec, network):
    
    pvc = {}
    if recordSpec is not None:
        for p in recordSpec:
            indices = recordSpec[p]
            if p=='all':
                for pop in network.populations:
                    pvc[pop.id] = _generate_cell_indices(pop.id, indices, network)
                    
            else:
                #pop = network.get_child(p, 'populations')
                pvc[p] = _generate_cell_indices(p, indices, network)
            
    return pvc
    
    
def _generate_cell_indices(pop_id, indices, network):
    
    a = []
    pop = network.get_child(pop_id, 'populations')
    
    if indices=='*':
        size = evaluate(pop.size, network.parameters)
        for i in range(size):
            a.append(i)
    if isinstance(indices, int):
        a.append(indices)
    if isinstance(indices, list):
        for i in indices:
            a.append(i)
    return a


def is_spiking_input_population(population, network):
    
    cell = network.get_child(population.component, 'cells')
    
    return is_spiking_input_cell(cell)


def is_spiking_input_cell(cell):
    if cell.pynn_cell:
        if cell.pynn_cell=="SpikeSourcePoisson":
            return True
        else:
            return False

def is_spiking_input_nml_cell(component_obj):
    if component_obj.__class__.__name__=='SpikeSourcePoisson':
        return True
    else:
        return False

        
def create_new_model(reference,
                     duration, 
                     dt=0.025, # ms 
                     temperature=6.3, # degC
                     default_region=None,
                     parameters = None,
                     cell_for_default_population=None,
                     color_for_default_population='0.8 0 0',
                     input_for_default_population=None,
                     synapses=[],
                     simulation_seed=12345,
                     network_filename=None,
                     simulation_filename=None):
        
    ################################################################################
    ###   Build a new network

    net = Network(id=reference)
    net.notes = "A network model: %s"%reference
    net.temperature = temperature # degC
    if parameters:
        net.parameters = parameters
    

    ################################################################################
    ###   Add some regions
    
    if default_region:
        if type(default_region)==str:
            r1 = RectangularRegion(id=default_region, x=0,y=0,z=0,width=1000,height=100,depth=1000)
            net.regions.append(r1)
            default_region = r1
        else:
            net.regions.append(default_region)


    ################################################################################
    ###   Add some cells

    if cell_for_default_population:
        net.cells.append(cell_for_default_population)


    ################################################################################
    ###   Add some synapses
    
    for s in synapses:
        net.synapses.append(s)



    ################################################################################
    ###   Add some populations

    if cell_for_default_population:
        pop = Population(id='pop_%s'%cell_for_default_population.id, 
                            size=1, 
                            component=cell_for_default_population.id, 
                            properties={'color':color_for_default_population})

        if default_region:
            pop.region = default_region
            
            pop.random_layout = RandomLayout(region=default_region.id)

        net.populations.append(pop)
        


    ################################################################################
    ###   Add a projection

    '''
    net.projections.append(Projection(id='proj0',
                                      presynaptic=p0.id, 
                                      postsynaptic=p1.id,
                                      synapse='ampa'))

    net.projections[0].random_connectivity=RandomConnectivity(probability=0.5)'''
    
 
    ################################################################################
    ###   Add some inputs
    
    if input_for_default_population:

        net.input_sources.append(input_for_default_population)

        
        net.inputs.append(Input(id='Stim_%s'%input_for_default_population.id,
                                input_source=input_for_default_population.id,
                                population=pop.id,
                                percentage=100))
        


    ################################################################################
    ###   Save to JSON format

    net.id = reference

    print(net.to_json())
    if network_filename==None:
        network_filename='%s.json'%net.id
    new_file = net.to_json_file(network_filename)
    

    ################################################################################
    ###   Build Simulation object & save as JSON

    sim = Simulation(id='Sim_%s'%reference,
                     network=new_file,
                     duration=duration,
                     dt=dt,
                     seed=simulation_seed,
                     recordTraces={'all':'*'})

    if simulation_filename==None:
        simulation_filename='%s.json'%sim.id
    sim.to_json_file(simulation_filename)
    
    return sim, net
