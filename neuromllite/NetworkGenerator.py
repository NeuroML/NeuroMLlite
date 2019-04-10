import copy
from neuromllite.utils import evaluate
from neuromllite.utils import load_network_json
from neuromllite.utils import print_v
import numpy as np
import os
import random


def _locate_file(f, base_dir):
    """
    Utility method for finding full path to a filename as string
    """
    if base_dir == None:
        return f
    file_name = os.path.join(base_dir, f)
    real = os.path.realpath(file_name)
    #print_v('- Located %s at %s'%(f,real))
    return real


def generate_network(nl_model, 
                     handler, 
                     seed=1234, 
                     always_include_props=False,
                     include_connections=True,
                     include_inputs=True,
                     base_dir=None):
    """
    Generate the network model as described in NeuroMLlite in a specific handler,
    e.g. NeuroMLHandler, PyNNHandler, etc.
    """
    
    pop_locations = {}
    cell_objects = {}
    synapse_objects = {}
    
    print_v("Starting net generation for %s%s..." % (nl_model.id, 
                                ' (base dir: %s)' % base_dir if base_dir else ''))
    rng = random.Random(seed)
    
    if nl_model.network_reader:
        
        exec('from neuromllite.%s import %s' % (nl_model.network_reader.type, nl_model.network_reader.type))
        
        exec('network_reader = %s()' % (nl_model.network_reader.type))
        network_reader.parameters = nl_model.network_reader.parameters
        
        network_reader.parse(handler)
        pop_locations = network_reader.get_locations()
        
    else:
        notes = "Generated network: %s" % nl_model.id
        notes += "\n    Generation seed: %i" % (seed)
        if nl_model.parameters:
            notes += "\n    NeuroMLlite parameters: " 
            for p in nl_model.parameters:
                notes += "\n        %s = %s" % (p, nl_model.parameters[p])
        handler.handle_document_start(nl_model.id, notes)
        temperature = '%sdegC' % nl_model.temperature if nl_model.temperature else None 
        handler.handle_network(nl_model.id, nl_model.notes, temperature=temperature)
        
    nml2_doc_temp = _extract_pynn_components_to_neuroml(nl_model)
    
    for c in nl_model.cells:
        
        if c.neuroml2_source_file:
            from pyneuroml import pynml
            nml2_doc = pynml.read_neuroml2_file(_locate_file(c.neuroml2_source_file, base_dir), 
                                                include_includes=True)
            cell_objects[c.id] = nml2_doc.get_by_id(c.id)
            
        if c.pynn_cell:
            cell_objects[c.id] = nml2_doc_temp.get_by_id(c.id)
            
            
    for s in nl_model.synapses:
        if s.neuroml2_source_file:
            from pyneuroml import pynml
            nml2_doc = pynml.read_neuroml2_file(_locate_file(s.neuroml2_source_file, base_dir), 
                                                include_includes=True)
            synapse_objects[s.id] = nml2_doc.get_by_id(s.id)
            
        if s.pynn_synapse:
            synapse_objects[s.id] = nml2_doc_temp.get_by_id(s.id)
            
            
    for p in nl_model.populations:
        
        size = evaluate(p.size, nl_model.parameters)
        properties = p.properties if p.properties else {}
        if p.random_layout:
            properties['region'] = p.random_layout.region
            
        if not p.random_layout and not p.single_location and not always_include_props:
            
            # If there are no positions (abstract network), and <property>
            # is added to <population>, jLems doesn't like it... (it has difficulty 
            # interpreting pop0[0]/v, etc.)
            # So better not to give properties...
            properties = {} 
            
        if p.notes:
            handler.handle_population(p.id, 
                                      p.component, 
                                      size, 
                                      cell_objects[p.component] if p.component in cell_objects else None,
                                      properties=properties,
                                      notes=p.notes)
        else:
            handler.handle_population(p.id, 
                                      p.component, 
                                      size, 
                                      cell_objects[p.component] if p.component in cell_objects else None,
                                      properties=properties)
                                 
        pop_locations[p.id] = np.zeros((size, 3))
        
        for i in range(size):
            if p.random_layout:
                region = nl_model.get_child(p.random_layout.region, 'regions')
                
                x = region.x + rng.random() * region.width
                y = region.y + rng.random() * region.height
                z = region.z + rng.random() * region.depth
                pop_locations[p.id][i] = (x, y, z)

                handler.handle_location(i, p.id, p.component, x, y, z)
                
            if p.single_location:
                loc = p.single_location.location
                x = loc.x
                y = loc.y
                z = loc.z
                pop_locations[p.id][i] = (x, y, z)

                handler.handle_location(i, p.id, p.component, x, y, z)
                
                
        if hasattr(handler, 'finalise_population'):
            handler.finalise_population(p.id)
        
    if include_connections:
        for p in nl_model.projections:

            type = p.type if p.type else 'projection'

            handler.handle_projection(p.id, 
                                      p.presynaptic, 
                                      p.postsynaptic, 
                                      p.synapse,
                                      synapse_obj=synapse_objects[p.synapse] if p.synapse in synapse_objects else None,
                                      pre_synapse_obj=synapse_objects[p.pre_synapse] if p.pre_synapse in synapse_objects else None,
                                      type=type)

            delay = p.delay if p.delay else 0
            weight = p.weight if p.weight else 1

            conn_count = 0
            if p.random_connectivity:
                for pre_i in range(len(pop_locations[p.presynaptic])):
                    for post_i in range(len(pop_locations[p.postsynaptic])):
                        flip = rng.random()
                        #print("Is cell %i conn to %i, prob %s - %s"%(pre_i, post_i, flip, p.random_connectivity.probability))
                        if flip < p.random_connectivity.probability:
                            weight = evaluate(weight, nl_model.parameters)
                            delay = evaluate(delay, nl_model.parameters)
                            #print_v("Adding connection %i with weight: %s, delay: %s"%(conn_count, weight, delay))
                            handler.handle_connection(p.id, 
                                                      conn_count, 
                                                      p.presynaptic, 
                                                      p.postsynaptic, 
                                                      p.synapse, \
                                                      pre_i, \
                                                      post_i, \
                                                      preSegId=0, \
                                                      preFract=0.5, \
                                                      postSegId=0, \
                                                      postFract=0.5, \
                                                      delay=delay, \
                                                      weight=weight)
                            conn_count += 1
                            
            if p.convergent_connectivity:
                
                for post_i in range(len(pop_locations[p.postsynaptic])):
                
                    for count in range(int(p.convergent_connectivity.num_per_post)):
                        found = False
                        while not found:
                            pre_i = int(rng.random()*len(pop_locations[p.presynaptic]))
                            if p.presynaptic==p.postsynaptic and pre_i==post_i:
                                found=False
                            else:
                                found=True

                        weight = evaluate(weight, nl_model.parameters)
                        delay = evaluate(delay, nl_model.parameters)
                        print_v("Adding connection %i (%i->%i; %i to %s of post) with weight: %s, delay: %s"%(conn_count, pre_i, post_i, count, p.convergent_connectivity.num_per_post, weight, delay))
                        handler.handle_connection(p.id, 
                                                  conn_count, 
                                                  p.presynaptic, 
                                                  p.postsynaptic, 
                                                  p.synapse, \
                                                  pre_i, \
                                                  post_i, \
                                                  preSegId=0, \
                                                  preFract=0.5, \
                                                  postSegId=0, \
                                                  postFract=0.5, \
                                                  delay=delay, \
                                                  weight=weight)
                        conn_count += 1

            elif p.one_to_one_connector:
                for i in range(min(len(pop_locations[p.presynaptic]), len(pop_locations[p.postsynaptic]))):
                    weight = evaluate(weight, nl_model.parameters)
                    delay = evaluate(delay, nl_model.parameters)
                    #print_v("Adding connection %i with weight: %s, delay: %s"%(conn_count, weight, delay))
                    handler.handle_connection(p.id, 
                                              conn_count, 
                                              p.presynaptic, 
                                              p.postsynaptic, 
                                              p.synapse, \
                                              i, \
                                              i, \
                                              preSegId=0, \
                                              preFract=0.5, \
                                              postSegId=0, \
                                              postFract=0.5, \
                                              delay=delay, \
                                              weight=weight)
                    conn_count += 1

            handler.finalise_projection(p.id, 
                                        p.presynaptic, 
                                        p.postsynaptic, 
                                        p.synapse)
                                 
    if include_inputs:   
        for input in nl_model.inputs:

            handler.handle_input_list(input.id, 
                                      input.population, 
                                      input.input_source, 
                                      size=0, 
                                      input_comp_obj=None)

            input_count = 0      
            for i in range(len(pop_locations[input.population])):
                flip = rng.random()
                weight = input.weight if input.weight else 1
                if flip * 100. < input.percentage:
                    
                    number_per_cell = evaluate(input.number_per_cell, nl_model.parameters) if input.number_per_cell else 1
                    
                    for j in range(number_per_cell):
                        handler.handle_single_input(input.id, 
                                                    input_count, 
                                                    i,
                                                    weight=evaluate(weight, nl_model.parameters))
                        input_count += 1

            handler.finalise_input_source(input.id)
            
    if hasattr(handler, 'finalise_document'):
        handler.finalise_document()
        
        
def check_to_generate_or_run(argv, sim):
    """
    Useful method for calling in main method after network and simulation are 
    generated, to handle some standard export options like -jnml, -graph etc.
    """
    
    print_v("Checking arguments: %s to see whether anything should be run in simulation %s (net: %s)..." % 
               (argv, sim.id, sim.network))
    
    if len(argv)==1:
        print_v("No arguments found. Currently supported export formats:")
        print_v("   -nml | -jnml | -jnmlnrn | -jnmlnetpyne | -netpyne | -pynnnrn "+\
                "| -pynnnest | -pynnbrian | -pynnneuroml | -sonata | -matrix[1-2] | -graph[1-6 n/d/f/c]")
        
    if '-pynnnest' in argv:
        generate_and_run(sim, simulator='PyNN_NEST')

    elif '-pynnnrn' in argv:
        generate_and_run(sim, simulator='PyNN_NEURON')

    elif '-pynnbrian' in argv:
        generate_and_run(sim, simulator='PyNN_Brian')

    elif '-jnml' in argv:
        generate_and_run(sim, simulator='jNeuroML')

    elif '-jnmlnrn' in argv:
        generate_and_run(sim, simulator='jNeuroML_NEURON')

    elif '-netpyne' in argv:
        generate_and_run(sim, simulator='NetPyNE')

    elif '-pynnneuroml' in argv:
        generate_and_run(sim, simulator='PyNN_NeuroML')

    elif '-sonata' in argv:
        generate_and_run(sim, simulator='sonata')
        
    elif '-nml' in argv or '-neuroml' in argv:
        
        network = load_network_json(sim.network)
        generate_neuroml2_from_network(network, validate=True)
        
    else:
        for a in argv:
            
            if '-jnmlnetpyne' in a:
                num_processors = 1
                if len(a)>len('-jnmlnetpyne'):
                    num_processors = int(a[12:])
                generate_and_run(sim, simulator='jNeuroML_NetPyNE',num_processors=num_processors)
            elif 'graph' in a: # e.g. -graph3c
                generate_and_run(sim, simulator=a[1:]) # Will not "run" obviously...
            elif 'matrix' in a: # e.g. -matrix2
                generate_and_run(sim, simulator=a[1:]) # Will not "run" obviously...
                
        
def _extract_pynn_components_to_neuroml(nl_model, nml_doc=None):
    """
    Parse the NeuroMLlite description for cell, synapses and inputs described as 
    PyNN elements (e.g. IF_cond_alpha, DCSource) and parameters, and convert 
    these to the equivalent elements in a NeuroMLDocument
    """
    
    if nml_doc == None:
        from neuroml import NeuroMLDocument
        nml_doc = NeuroMLDocument(id="temp")
    
    for c in nl_model.cells:
        
        if c.pynn_cell:
            
            if nml_doc.get_by_id(c.id) == None:
                import pyNN.neuroml
                cell_params = c.parameters if c.parameters else {}
                #print('------- %s: %s' % (c, cell_params))
                for p in cell_params:
                    cell_params[p] = evaluate(cell_params[p], nl_model.parameters)
                #print('====== %s: %s' % (c, cell_params))
                for proj in nl_model.projections:

                    synapse = nl_model.get_child(proj.synapse, 'synapses')
                    post_pop = nl_model.get_child(proj.postsynaptic, 'populations')
                    if post_pop.component == c.id:
                        #print("--------- Cell %s in post pop %s of %s uses %s"%(c.id,post_pop.id, proj.id, synapse))

                        if synapse.pynn_receptor_type == 'excitatory':
                            post = '_E'
                        elif synapse.pynn_receptor_type == 'inhibitory':
                            post = '_I'
                        for p in synapse.parameters:
                            cell_params['%s%s' % (p, post)] = synapse.parameters[p]

                temp_cell = eval('pyNN.neuroml.%s(**cell_params)' % c.pynn_cell)
                if c.pynn_cell != 'SpikeSourcePoisson':
                    temp_cell.default_initial_values['v'] = temp_cell.parameter_space['v_rest'].base_value

                cell_id = temp_cell.add_to_nml_doc(nml_doc, None)
                cell = nml_doc.get_by_id(cell_id)
                cell.id = c.id
            
    for s in nl_model.synapses:
        if nml_doc.get_by_id(s.id) == None:
            
            if s.pynn_synapse_type and s.pynn_receptor_type:
                import neuroml
                
                if s.pynn_synapse_type == 'cond_exp':
                    syn = neuroml.ExpCondSynapse(id=s.id, tau_syn=s.parameters['tau_syn'], e_rev=s.parameters['e_rev'])
                    nml_doc.exp_cond_synapses.append(syn)
                elif s.pynn_synapse_type == 'cond_alpha':
                    syn = neuroml.AlphaCondSynapse(id=s.id, tau_syn=s.parameters['tau_syn'], e_rev=s.parameters['e_rev'])
                    nml_doc.alpha_cond_synapses.append(syn)
                elif s.pynn_synapse_type == 'curr_exp':
                    syn = neuroml.ExpCurrSynapse(id=s.id, tau_syn=s.parameters['tau_syn'])
                    nml_doc.exp_curr_synapses.append(syn)
                elif s.pynn_synapse_type == 'curr_alpha':
                    syn = neuroml.AlphaCurrSynapse(id=s.id, tau_syn=s.parameters['tau_syn'])
                    nml_doc.alpha_curr_synapses.append(syn)
    
    for i in nl_model.input_sources:
        
        #if nml_doc.get_by_id(i.id) == None:
      
        if i.pynn_input:
            import pyNN.neuroml
            input_params = i.parameters if i.parameters else {}
            exec('input__%s = pyNN.neuroml.%s(**input_params)' % (i.id, i.pynn_input))
            exec('temp_input = input__%s' % i.id)
            pg_id = temp_input.add_to_nml_doc(nml_doc, None)
            #for pp in nml_doc.pulse_generators:
            #    print('PG: %s: %s'%(pp,pp.id))
            pg = nml_doc.get_by_id(pg_id)
            pg.id = i.id
            
    return nml_doc
        
        
def generate_neuroml2_from_network(nl_model, 
                                   nml_file_name=None, 
                                   print_summary=True, 
                                   seed=1234, 
                                   format='xml', 
                                   base_dir=None,
                                   copy_included_elements=False,
                                   target_dir=None,
                                   validate=False):
    """
    Generate and save NeuroML2 file (in either XML or HDF5 format) from the 
    NeuroMLlite description
    """

    print_v("Generating NeuroML2 for %s%s..." % (nl_model.id, ' (base dir: %s; target dir: %s)' 
                 % (base_dir, target_dir) if base_dir or target_dir else ''))
    
    import neuroml
    from neuroml.hdf5.NetworkBuilder import NetworkBuilder

    neuroml_handler = NetworkBuilder()

    generate_network(nl_model, neuroml_handler, seed=seed, base_dir=base_dir)

    nml_doc = neuroml_handler.get_nml_doc()
    
    for i in nl_model.input_sources:
        
        if nml_doc.get_by_id(i.id) == None:
            if i.neuroml2_source_file:
                
                incl = neuroml.IncludeType(_locate_file(i.neuroml2_source_file, base_dir))
                if not incl in nml_doc.includes:
                    nml_doc.includes.append(incl)
                                        
            if i.neuroml2_input: 
                input_params = i.parameters if i.parameters else {}
                
                # TODO make more generic...
                
                if i.neuroml2_input.lower() == 'pulsegenerator':
                    input = neuroml.PulseGenerator(id=i.id)
                    nml_doc.pulse_generators.append(input)
                    
                elif i.neuroml2_input.lower() == 'pulsegeneratordl':
                    input = neuroml.PulseGeneratorDL(id=i.id)
                    nml_doc.pulse_generator_dls.append(input)

                elif i.neuroml2_input.lower() == 'poissonfiringsynapse':
                    input = neuroml.PoissonFiringSynapse(id=i.id)
                    nml_doc.poisson_firing_synapses.append(input)

                for p in input_params:
                    exec('input.%s = "%s"' % (p, evaluate(input_params[p], nl_model.parameters)))
                
    for c in nl_model.cells:
        if c.neuroml2_source_file:
            
            incl = neuroml.IncludeType(_locate_file(c.neuroml2_source_file, base_dir))
            found_cell = False
            for cell in nml_doc.cells:
                if cell.id == c.id:
                    nml_doc.cells.remove(cell) # Better to use imported cell file; will have channels, etc.
                    nml_doc.includes.append(incl) 
                    found_cell = True
                    
            if not found_cell:
                for p in nl_model.populations:
                    if p.component == c.id:
                        pass
            
            if not incl in nml_doc.includes:
                nml_doc.includes.append(incl) 
                
        '''  Needed???
        if c.lems_source_file:      
            incl = neuroml.IncludeType(_locate_file(c.lems_source_file, base_dir))
            if not incl in nml_doc.includes:
                nml_doc.includes.append(incl)'''
                
        if c.neuroml2_cell: 
            
            cell_params = c.parameters if c.parameters else {}
            # TODO make more generic...
            if c.neuroml2_cell.lower() == 'spikegenerator':
                cell = neuroml.SpikeGenerator(id=c.id)
                nml_doc.spike_generators.append(cell)
            elif c.neuroml2_cell.lower() == 'spikegeneratorpoisson':
                cell = neuroml.SpikeGeneratorPoisson(id=c.id)
                nml_doc.spike_generator_poissons.append(cell)
            elif c.neuroml2_cell.lower() == 'spikegeneratorrefpoisson':
                cell = neuroml.SpikeGeneratorRefPoisson(id=c.id)
                nml_doc.spike_generator_ref_poissons.append(cell)
            else:
                raise Exception('The neuroml2_cell: %s is not yet supported...'%c.neuroml2_cell)

            for p in cell_params:
                exec('cell.%s = "%s"' % (p, evaluate(cell_params[p], nl_model.parameters)))
                
    for s in nl_model.synapses:
        if nml_doc.get_by_id(s.id) == None:
            if s.neuroml2_source_file:
                incl = neuroml.IncludeType(_locate_file(s.neuroml2_source_file, base_dir))
                if not incl in nml_doc.includes:
                    nml_doc.includes.append(incl) 
                    
       
    # Look for and add the PyNN based elements to the NeuroMLDocument 
    _extract_pynn_components_to_neuroml(nl_model, nml_doc)
                    
    if print_summary:
        # Print info
        print_v(nml_doc.summary())

    # Save to file
    if target_dir == None:
        target_dir = base_dir
    if format == 'xml':
        if not nml_file_name:
            nml_file_name = _locate_file('%s.net.nml' % nml_doc.id, target_dir)
        from neuroml.writers import NeuroMLWriter
        NeuroMLWriter.write(nml_doc, nml_file_name)
        
    if format == 'hdf5':
        if not nml_file_name:
            nml_file_name = _locate_file('%s.net.nml.h5' % nml_doc.id, target_dir)
        from neuroml.writers import NeuroMLHdf5Writer
        NeuroMLHdf5Writer.write(nml_doc, nml_file_name)

    print_v("Written NeuroML to %s" % nml_file_name)
    
    if validate and format == 'xml':
        
        from pyneuroml import pynml
        success = pynml.validate_neuroml2(nml_file_name, verbose_validate=False)
        if success:
            print_v('Generated file is valid NeuroML2!')
        else:
            print_v('Generated file is NOT valid NeuroML2!')
            
    
    return nml_file_name, nml_doc


locations_mods_loaded_from = []

def _generate_neuron_files_from_neuroml(network, verbose=False, dir_for_mod_files = None):
    """
    Generate NEURON hoc/mod files from the NeuroML files which are marked as 
    included in the NeuroMLlite description; also compiles the mod files
    """

    print_v("-------------   Generating NEURON files from NeuroML for %s (default dir: %s)..." % (network.id, dir_for_mod_files))
    nml_src_files = []

    from neuroml import NeuroMLDocument
    import neuroml.writers as writers
    temp_nml_doc = NeuroMLDocument(id="temp")
    
    dirs_for_mod_files = []
    if dir_for_mod_files!=None:
        dirs_for_mod_files.append(os.path.abspath(dir_for_mod_files))

    for c in network.cells:
        if c.neuroml2_source_file:
            nml_src_files.append(c.neuroml2_source_file)
            dir_for_mod = os.path.dirname(os.path.abspath(c.neuroml2_source_file))
            if not dir_for_mod in dirs_for_mod_files: dirs_for_mod_files.append(dir_for_mod)
                
    for s in network.synapses:
        if s.neuroml2_source_file:
            nml_src_files.append(s.neuroml2_source_file)
            dir_for_mod = os.path.dirname(os.path.abspath(s.neuroml2_source_file))
            if not dir_for_mod in dirs_for_mod_files: dirs_for_mod_files.append(dir_for_mod)

    for i in network.input_sources:
        if i.neuroml2_source_file:
            nml_src_files.append(i.neuroml2_source_file)
            dir_for_mod = os.path.dirname(os.path.abspath(i.neuroml2_source_file))
            if not dir_for_mod in dirs_for_mod_files: dirs_for_mod_files.append(dir_for_mod)
                
    temp_nml_doc = _extract_pynn_components_to_neuroml(network)
      
    summary = temp_nml_doc.summary()
    
    if 'IF_' in summary: 
        import tempfile
        temp_nml_file = tempfile.NamedTemporaryFile(delete=False, suffix='.nml', dir=dir_for_mod_files)
        print_v("Writing temporary NML file to: %s, summary: "%temp_nml_file.name)
        print_v(summary)

        writers.NeuroMLWriter.write(temp_nml_doc, temp_nml_file.name)
        nml_src_files.append(temp_nml_file.name)

    for f in nml_src_files:
        from pyneuroml import pynml
        print_v("Generating/compiling hoc/mod files for: %s"%f)
        pynml.run_lems_with_jneuroml_neuron(f, 
                                            nogui=True, 
                                            only_generate_scripts=True,
                                            compile_mods=True,
                                            verbose=False)

    for dir_for_mod_files in dirs_for_mod_files:
        if not dir_for_mod_files in locations_mods_loaded_from:
            print_v("Generated NEURON code; loading mechanisms from %s (cwd: %s; already loaded: %s)" % (dir_for_mod_files,os.getcwd(),locations_mods_loaded_from))
            try:

                from neuron import load_mechanisms
                if os.getcwd()==dir_for_mod_files:
                    print_v("That's current dir => importing neuron module loads mods here...")
                else:
                    load_mechanisms(dir_for_mod_files)
                locations_mods_loaded_from.append(dir_for_mod_files)
            except:
                print_v("Failed to load mod file mechanisms...")
        else:
            print_v("Already loaded mechanisms from %s (all loaded: %s)" % (dir_for_mod_files,locations_mods_loaded_from))


def generate_and_run(simulation, 
                     simulator, 
                     network=None, 
                     return_results=False, 
                     base_dir=None,
                     target_dir=None,
                     num_processors=1):
    """
    Generates the network in the specified simulator and runs, if appropriate
    """

    if network == None:
        network = load_network_json(simulation.network)
    
    print_v("Generating network %s and running in simulator: %s..." % (network.id, simulator))
    
    if simulator == 'NEURON':
        
        _generate_neuron_files_from_neuroml(network, dir_for_mod_files=target_dir)
        
        from neuromllite.NeuronHandler import NeuronHandler
        
        nrn_handler = NeuronHandler()

        for c in network.cells:
            if c.neuroml2_source_file:
                src_dir = os.path.dirname(os.path.abspath(c.neuroml2_source_file))
                nrn_handler.executeHoc('load_file("%s/%s.hoc")' % (src_dir, c.id))
                
        generate_network(network, nrn_handler, generate_network, base_dir)
        if return_results:
            raise NotImplementedError("Reloading results not supported in Neuron yet...")


    elif simulator.lower() == 'sonata': # Will not "run" obviously...
        
        from neuromllite.SonataHandler import SonataHandler
        
        sonata_handler = SonataHandler()
        
        generate_network(network, sonata_handler, always_include_props=True, base_dir=base_dir)
    
        print_v("Done with Sonata...")


    elif simulator.lower().startswith('graph'): # Will not "run" obviously...
                           
        from neuromllite.GraphVizHandler import GraphVizHandler, engines
        

        try:
            if simulator[-1].isalpha():
                print simulator
                print simulator[5:]
                print simulator[5:-1]
                engine = engines[simulator[-1]]
                level = int(simulator[5:-1])
            else:
                engine = 'dot'
                level = int(simulator[5:])
        
        except Exception as e:
            print e
            print_v("Error parsing: %s"%simulator)
            print_v("Graphs of the network structure can be generated at many levels of detail (1-6, required) and laid out using GraphViz engines (d - dot (default); c - circo; n - neato; f - fdp), so use: -graph3c, -graph2, -graph4f etc.")
            return
        
        handler = GraphVizHandler(level, engine=engine, nl_network=network)
        
        generate_network(network, handler, always_include_props=True, base_dir=base_dir)
    
        print_v("Done with GraphViz...")
        
        
    elif simulator.lower().startswith('matrix'): # Will not "run" obviously...
                           
        from neuromllite.MatrixHandler import MatrixHandler
        
        try:
            level = int(simulator[6:])
        except:
            print_v("Error parsing: %s"%simulator)
            print_v("Matrices of the network structure can be generated at many levels of detail (1-n, required), so use: -matrix1, -matrix2, etc.")
            return
        
        handler = MatrixHandler(level, nl_network=network)
        
        generate_network(network, handler, always_include_props=True, base_dir=base_dir)
    
        print_v("Done with MatrixHandler...")
        

    elif simulator.startswith('PyNN'):
        
        #_generate_neuron_files_from_neuroml(network)
        simulator_name = simulator.split('_')[1].lower()
        
        
        from neuromllite.PyNNHandler import PyNNHandler
        
        pynn_handler = PyNNHandler(simulator_name, simulation.dt, network.id)
        
        syn_cell_params = {}
        for proj in network.projections:
            
            synapse = network.get_child(proj.synapse, 'synapses')
            post_pop = network.get_child(proj.postsynaptic, 'populations')
          
            if not post_pop.component in syn_cell_params:
                syn_cell_params[post_pop.component] = {}
            for p in synapse.parameters:
                post = ''
                if synapse.pynn_receptor_type == "excitatory":
                    post = '_E'
                elif synapse.pynn_receptor_type == "inhibitory":
                    post = '_I'
                syn_cell_params[post_pop.component]['%s%s' % (p, post)] = synapse.parameters[p]
                    
        
        cells = {}
        for c in network.cells:
            if c.pynn_cell:
                cell_params = {}
                if c.parameters: 
                    for p in c.parameters:
                        cell_params[p] = evaluate(c.parameters[p], network.parameters)
                
                dont_set_here = ['tau_syn_E', 'e_rev_E', 'tau_syn_I', 'e_rev_I']
                for d in dont_set_here:
                    if d in c.parameters:
                        raise Exception('Synaptic parameters like %s should be set '+
                          'in individual synapses, not in the list of parameters associated with the cell' % d)
                if c.id in syn_cell_params:
                    cell_params.update(syn_cell_params[c.id])
                print_v("Creating cell with params: %s" % cell_params)
                exec('cells["%s"] = pynn_handler.sim.%s(**cell_params)' % (c.id, c.pynn_cell))
                
                if c.pynn_cell != 'SpikeSourcePoisson':
                    exec("cells['%s'].default_initial_values['v'] = cells['%s'].parameter_space['v_rest'].base_value" % (c.id, c.id))
                
        pynn_handler.set_cells(cells)
        
        receptor_types = {}
        for s in network.synapses:
            if s.pynn_receptor_type:
                receptor_types[s.id] = s.pynn_receptor_type
                
        pynn_handler.set_receptor_types(receptor_types)
        
        for input_source in network.input_sources:
            if input_source.pynn_input:
                pynn_handler.add_input_source(input_source)
        
        generate_network(network, pynn_handler, always_include_props=True, base_dir=base_dir)
        
        for pid in pynn_handler.populations:
            pop = pynn_handler.populations[pid]
            if 'all' in simulation.recordTraces or pop.label in simulation.recordTraces:
                if pop.can_record('v'):
                    pop.record('v')
        
        
        pynn_handler.sim.run(simulation.duration)
        pynn_handler.sim.end()
        
        traces = {}
        events = {}
        
        if not 'NeuroML' in simulator:
            from neo.io import PyNNTextIO

            for pid in pynn_handler.populations:
                pop = pynn_handler.populations[pid]

                if 'all' in simulation.recordTraces or pop.label in simulation.recordTraces:
                    
                    filename = "%s.%s.v.dat" % (simulation.id, pop.label)
                    all_columns = []
                    print_v("Writing data for %s to %s" % (pop.label, filename))
                    for i in range(len(pop)):
                        if pop.can_record('v'):
                            ref = '%s[%i]'%(pop.label,i)
                            traces[ref] = []
                            data = pop.get_data('v', gather=False)
                            for segment in data.segments:
                                vm = segment.analogsignals[0].transpose()[i]
                                
                                if len(all_columns) == 0:
                                    tt = np.array([t * simulation.dt / 1000. for t in range(len(vm))])
                                    all_columns.append(tt)
                                vm_si = [float(v / 1000.) for v in vm]
                                traces[ref] = vm_si
                                all_columns.append(vm_si)
                                
                            times_vm = np.array(all_columns).transpose()
                                
                    np.savetxt(filename, times_vm, delimiter='\t', fmt='%s')
          
        
        if return_results:
            _print_result_info(traces, events)
            return traces, events

    elif simulator == 'NetPyNE':
        
        if target_dir==None:
            target_dir='./'
            
        _generate_neuron_files_from_neuroml(network, dir_for_mod_files=target_dir)
        
        from netpyne import specs
        from netpyne import sim
        # Note NetPyNE from this branch is required: https://github.com/Neurosim-lab/netpyne/tree/neuroml_updates
        from netpyne.conversion.neuromlFormat import NetPyNEBuilder
        
        import pprint; pp = pprint.PrettyPrinter(depth=6)
        
        netParams = specs.NetParams()
        simConfig = specs.SimConfig()
        netpyne_handler = NetPyNEBuilder(netParams, simConfig=simConfig, verbose=True)
        
        generate_network(network, netpyne_handler, base_dir=base_dir)
        
        netpyne_handler.finalise()
        
        simConfig = specs.SimConfig() 
        simConfig.tstop = simulation.duration
        simConfig.duration = simulation.duration
        simConfig.dt = simulation.dt
        simConfig.seed = simulation.seed
        simConfig.recordStep = simulation.dt
        
        simConfig.recordCells = ['all'] 
        simConfig.recordTraces = {}
        

        for pop in netpyne_handler.popParams.values():
            if 'all' in simulation.recordTraces or pop.id in simulation.recordTraces:
                for i in pop['cellsList']:
                    id = pop['pop']
                    index = i['cellLabel']
                    simConfig.recordTraces['v_%s_%s' % (id, index)] = {'sec':'soma', 'loc':0.5, 'var':'v', 'conds':{'pop':id, 'cellLabel':index}}

        simConfig.saveDat = True
        
        print_v("NetPyNE netParams: ")
        pp.pprint(netParams.todict())
        #print_v("NetPyNE simConfig: ")
        #pp.pprint(simConfig.todict())
        
        sim.initialize(netParams, simConfig)  # create network object and set cfg and net params

        sim.net.createPops()  
        cells = sim.net.createCells()                 # instantiate network cells based on defined populations  
        
        
        for proj_id in netpyne_handler.projection_infos.keys():
            projName, prePop, postPop, synapse, ptype = netpyne_handler.projection_infos[proj_id]
            print_v("Creating connections for %s (%s): %s->%s via %s" % (projName, ptype, prePop, postPop, synapse))
            
            preComp = netpyne_handler.pop_ids_vs_components[prePop]
            
            for conn in netpyne_handler.connections[projName]:
                
                pre_id, pre_seg, pre_fract, post_id, post_seg, post_fract, delay, weight = conn
                
                #connParam = {'delay':delay,'weight':weight,'synsPerConn':1, 'sec':post_seg, 'loc':post_fract, 'threshold':threshold}
                connParam = {'delay':delay, 'weight':weight, 'synsPerConn':1, 'sec':post_seg, 'loc':post_fract}
                
                if ptype == 'electricalProjection':

                    if weight != 1:
                        raise Exception('Cannot yet support inputs where weight !=1!')
                    connParam = {'synsPerConn': 1, 
                        'sec': post_seg, 
                        'loc': post_fract, 
                        'gapJunction': True, 
                        'weight': weight}
                else:
                    connParam = {'delay': delay,
                        'weight': weight,
                        'synsPerConn': 1, 
                        'sec': post_seg, 
                        'loc': post_fract} 
                        #'threshold': threshold}

                connParam['synMech'] = synapse

                if post_id in sim.net.gid2lid:  # check if postsyn is in this node's list of gids
                    sim.net._addCellConn(connParam, pre_id, post_id)
                    
                    
        stims = sim.net.addStims()                    # add external stimulation to cells (IClamps etc)
        simData = sim.setupRecording()              # setup variables to record for each cell (spikes, V traces, etc)
        sim.runSim()                      # run parallel Neuron simulation  
        sim.gatherData()                  # gather spiking data and cell info from each node
        sim.saveData()                    # save params, cell info and sim output to file (pickle,mat,txt,etc)
        
        if return_results:
            raise NotImplementedError("Reloading results not supported in NetPyNE yet...")
        
    elif simulator == 'jNeuroML' or  simulator == 'jNeuroML_NEURON' or simulator == 'jNeuroML_NetPyNE':

        from pyneuroml.lems import generate_lems_file_for_neuroml
        from pyneuroml import pynml

        lems_file_name = 'LEMS_%s.xml' % simulation.id

        nml_file_name, nml_doc = generate_neuroml2_from_network(network, base_dir=base_dir, target_dir=target_dir)
        included_files = ['PyNN.xml']

        for c in network.cells:        
            if c.lems_source_file:
                included_files.append(c.lems_source_file)
        '''
        if network.cells:
            for c in network.cells:
                included_files.append(c.neuroml2_source_file)
        '''
        if network.synapses:
            for s in network.synapses:  
                if s.lems_source_file:
                    included_files.append(s.lems_source_file)
                
        print_v("Generating LEMS file prior to running in %s" % simulator)
        
        pops_plot_save = []
        pops_spike_save = []
        gen_plots_for_quantities = {}
        gen_saves_for_quantities = {}
        
        for p in network.populations:
            
            if simulation.recordTraces and ('all' in simulation.recordTraces or p.id in simulation.recordTraces):
                pops_plot_save.append(p.id)
                
            if simulation.recordSpikes and ('all' in simulation.recordSpikes or p.id in simulation.recordSpikes):
                pops_spike_save.append(p.id)
                
            if simulation.recordRates and ('all' in simulation.recordRates or p.id in simulation.recordRates):
                size = evaluate(p.size, network.parameters)
                for i in range(size):
                    quantity = '%s/%i/%s/r' % (p.id, i, p.component)
                    gen_plots_for_quantities['%s_%i_r' % (p.id, i)] = [quantity]
                    gen_saves_for_quantities['%s_%i.r.dat' % (p.id, i)] = [quantity]
                
            if simulation.recordVariables:
                for var in simulation.recordVariables:
                    to_rec = simulation.recordVariables[var]
                    if ('all' in to_rec or p.id in to_rec):
                        size = evaluate(p.size, network.parameters)
                        for i in range(size):
                            quantity = '%s/%i/%s/%s' % (p.id, i, p.component,var)
                            gen_plots_for_quantities['%s_%i_%s' % (p.id, i, var)] = [quantity]
                            gen_saves_for_quantities['%s_%i.%s.dat' % (p.id, i, var)] = [quantity]
                
        
        generate_lems_file_for_neuroml(simulation.id, 
                                       nml_file_name, 
                                       network.id, 
                                       simulation.duration, 
                                       simulation.dt, 
                                       lems_file_name,
                                       target_dir=target_dir if target_dir else '.',
                                       nml_doc=nml_doc, # Use this if the nml doc has already been loaded (to avoid delay in reload)
                                       include_extra_files=included_files,
                                       
                                       gen_plots_for_all_v=False,
                                       plot_all_segments=False,
                                       gen_plots_for_quantities=gen_plots_for_quantities, # Dict with displays vs lists of quantity paths
                                       gen_plots_for_only_populations=pops_plot_save, # List of populations, all pops if = []
                                       
                                       gen_saves_for_all_v=False,
                                       save_all_segments=False,
                                       gen_saves_for_only_populations=pops_plot_save, # List of populations, all pops if = []
                                       gen_saves_for_quantities=gen_saves_for_quantities, # Dict with file names vs lists of quantity paths
                                       
                                       gen_spike_saves_for_all_somas=False,
                                       gen_spike_saves_for_only_populations=pops_spike_save, # List of populations, all pops if = []
                                       gen_spike_saves_for_cells={}, # Dict with file names vs lists of quantity paths
                                       spike_time_format='ID_TIME',
                                       
                                       copy_neuroml=True,
                                       lems_file_generate_seed=12345,
                                       report_file_name='report.%s.txt' % simulation.id,
                                       simulation_seed=simulation.seed if simulation.seed else 12345,
                                       verbose=True)
              
        lems_file_name = _locate_file(lems_file_name, target_dir)
        
        if simulator == 'jNeuroML':
            results = pynml.run_lems_with_jneuroml(lems_file_name, 
                                                   nogui=True, 
                                                   load_saved_data=return_results, 
                                                   reload_events=return_results)
        elif simulator == 'jNeuroML_NEURON':
            results = pynml.run_lems_with_jneuroml_neuron(lems_file_name, 
                                                          nogui=True, 
                                                          load_saved_data=return_results, 
                                                          reload_events=return_results)
        elif simulator == 'jNeuroML_NetPyNE':
            results = pynml.run_lems_with_jneuroml_netpyne(lems_file_name, 
                                                           nogui=True, 
                                                           verbose=True, 
                                                           load_saved_data=return_results, 
                                                           reload_events=return_results,
                                                           num_processors=num_processors)

        print_v("Finished running LEMS file %s in %s (returning results: %s)" % (lems_file_name, simulator, return_results))

        if return_results:
            traces, events = results
            _print_result_info(traces, events)
            return results # traces, events =
        
        
def _print_result_info(traces, events):
    """
    Print a summary of the returned (voltage) traces and spike times
    """
    print_v('Returning %i traces:'%len(traces))
    for r in sorted(traces.keys()):
        x = traces[r]
        print_v('  %s (%s): %s -> %s (min: %s, max: %s, len: %i)'%(r, type(x), x[0],x[-1],min(x),max(x),len(x)))
    print_v('Returning %i events:'%len(events))
    for r in sorted(events.keys()):
        x = events[r]
        print_v('  %s: %s -> %s (len: %i)'%(r, x[0] if len(x)>0 else '-',x[-1] if len(x)>0 else '-',len(x)))