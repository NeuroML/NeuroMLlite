import os

from neuromllite.utils import load_simulation_json,load_network_json
from neuromllite.NetworkGenerator import generate_and_run
from pyneuroml.pynml import get_value_in_si

from pyneuroml import pynml
from pyelectro import analysis
from collections import OrderedDict

import pprint; pp = pprint.PrettyPrinter(depth=6)

from neuromllite.utils import print_v


'''


        Work in progress!!!
        
        
'''

class ParameterSweep():
    
    def __init__(self, runner, vary, fixed={}, verbose=False):

        print_v("Initialising ParameterSweep with %s, %s" % (vary, fixed))
        self.runner = runner
        self.fixed = fixed
        self.vary = vary
        self.verbose=verbose
        self.complete = 0
        self.total_todo = 1
        self.report = OrderedDict()
        for v in vary:
            self.total_todo *= len(vary[v])
            
        self.analysis_var={'peak_delta':0,'baseline':0,'dvdt_threshold':0, 'peak_threshold':0}


    def _rem_key(self, d, key):
        r = dict(d)
        del r[key]
        return r


    def _run_instance(self, ** kwargs):

        print_v('============================================================= \n\n'+
                '     Instance (%s/%s): %s\n' % (self.complete, self.total_todo, kwargs))

        return self.runner.run_once( ** kwargs)


    def _sweep(self, v, f, reference=''):

        #print_v("  VAR: <%s>\n  FIX <%s>"%(v,f))
        keys = list(v)

        if len(keys) > 1:
            vals = v[keys[0]]
            others = v
            others = self._rem_key(others, keys[0])
            for val in vals:
                all_params = dict(f)
                all_params[keys[0]] = val

                self._sweep(others, all_params, reference='%s-%s%s' % (reference, keys[0], val))

        else:
            vals = v[keys[0]]
            for val in vals:
                all_params = dict(f)
                all_params[keys[0]] = val
                r = '%s_%s%s' % (reference, keys[0], val)
                ref_here = 'REFb%s%s' % (self.complete, r)
                all_params['reference'] = ref_here
                self.report[ref_here] = OrderedDict()
                self.report[ref_here]['parameters'] = all_params
                traces, events = self._run_instance( ** all_params)
                
                times = [t*1000. for t in traces['t']]
                volts = OrderedDict()
                for tr in traces:
                    if tr.endswith('/v'): volts[tr] = [v*1000. for v in traces[tr]]

                analysis_data=analysis.NetworkAnalysis(volts,
                                                   times,
                                                   self.analysis_var,
                                                   start_analysis=0,
                                                   end_analysis=times[-1],
                                                   smooth_data=False,
                                                   show_smoothed_data=False,
                                                   verbose=self.verbose)
                                                   
                analysed = analysis_data.analyse()
                
                self.report[ref_here]['analysis'] = OrderedDict()
                for a in analysed:
                    ref,var = a.split(':')
                    if not ref in self.report[ref_here]['analysis']:
                        self.report[ref_here]['analysis'][ref] = OrderedDict()
                    self.report[ref_here]['analysis'][ref][var] = analysed[a]
                    
                #self.report[ref_here]['parameters']
                
                self.complete += 1
            

    def run(self):

        print_v("Running...")
        self._sweep(self.vary, self.fixed)
        self.runner.finish()
        
        return self.report
    
    
    def plotLines(self, param, value, save_figure_to=None):
        
        all_pvals = OrderedDict()
        all_lines = OrderedDict()
        
        for ref, info in self.report.items():
            print_v('Checking %s: %s'%(ref,info['parameters']))
            pval = get_value_in_si(info['parameters'][param])

            for cell_ref in info['analysis']:
                if not cell_ref in all_lines:
                    all_lines[cell_ref] = []
                    all_pvals[cell_ref] = []
                vval = info['analysis'][cell_ref][value]
                
                all_lines[cell_ref].append(vval)
                all_pvals[cell_ref].append(pval)
        
        #print_v('Plot x: %s'%all_pvals)
        #print_v('Plot y: %s'%all_lines)
        xs= []
        ys = []
        labels = []
        markers = []
        
        for ref in all_lines:
            xs.append(all_pvals[ref])
            ys.append(all_lines[ref])
            labels.append(ref)
            markers.append('o')
        
        ax = pynml.generate_plot(xs,                  
                                 ys,           
                                 "Plot of %s vs %s"%(value, param),              
                                 xaxis = param,            
                                 yaxis = value,          
                                 labels = labels,       
                                 markers = markers,  
                                 show_plot_already=False,
                                 save_figure_to=save_figure_to)     # Save figure
        
class NeuroMLliteRunner():
    
    
    def __init__(self, nmllite_sim, plot_all=True):
        self.plot_all = plot_all
        self.base_dir = os.path.dirname(os.path.realpath(nmllite_sim))
        self.sim = load_simulation_json(nmllite_sim)
        
        if self.plot_all:
            from matplotlib import pyplot as plt
            plt.figure()
            self.ax = pynml.generate_plot([],                    
                         [],                   # Add 2 sets of y values
                         "Some traces...",                  # Title
                         labels = [],
                         xaxis = 'Time (ms)',            # x axis legend
                         yaxis = '???',   # y axis legend
                         show_plot_already=False)     # Save figure

        
    def run_once(self, ** kwargs):
        print_v('Running NeuroMLlite simulation...')
        
        network = load_network_json(self.base_dir+'/'+self.sim.network)
        for a in kwargs:
            network.parameters[a] = kwargs[a]
        
        traces, events = generate_and_run(self.sim, 
                                          simulator='jNeuroML', 
                                          network=network, 
                                          return_results=True,
                                          base_dir=self.base_dir)
                                          
        print_v("Returned traces: %s, events: %s"%(traces.keys(), events.keys()))
        
        if self.plot_all:
            for y in traces.keys():
                if y!='t':
                    label = '%s (%s)'%(y, kwargs)
                    self.ax.plot(traces['t'],traces[y],label=label)
                    
        return traces, events 
                    
                    
    def finish(self):
        from matplotlib import pyplot as plt
        if self.plot_all:
            plt.show()
        

if __name__ == '__main__':


    fixed = {'dt':0.025}
    fixed = {'N':20}

    quick = False
    #quick=True


    vary = {'stim_amp':['%spA'%(i/10.0) for i in xrange(-10,20,2)]}
    vary = {'stim_amp':['%spA'%(i/10.0) for i in xrange(-10,20,5)]}
    vary = {'weightInput':[1,2,5,10]}
    vary = {'weightInput':[1,2,3,20]}
    #vary = {'stim_amp':['1.5pA']}
    
    
    nmllr = NeuroMLliteRunner('../../examples/SimExample8.json')

    if quick:
        pass

    ps = ParameterSweep(nmllr, vary, fixed)

    report = ps.run()
    for r in report:
        print_v('--- REP: %s'%r)
        import json
        
        print_v(json.dumps(report[r], indent=4))
    
    #  ps.plotLines('weightInput','average_last_1percent',save_figure_to='average_last_1percent.png')
    ps.plotLines('weightInput','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
    
    import matplotlib.pyplot as plt
    
    plt.show()
    
    '''
    vary['i'] = [1,2,3]

    ps = ParameterSweep(vary,fixed)

    ps.run()'''