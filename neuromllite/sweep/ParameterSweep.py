import os

from neuromllite.utils import load_simulation_json,load_network_json
from neuromllite.NetworkGenerator import generate_and_run
from pyneuroml.pynml import get_value_in_si

from pyneuroml import pynml
from pyelectro import analysis
from collections import OrderedDict

from neuromllite.utils import print_v

from matplotlib import pyplot as plt
import numpy as np

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
        self.report['Varied parameters'] = vary
        self.report['Fixed parameters'] = fixed
        self.report['Simulations'] = OrderedDict()
        for v in vary:
            self.total_todo *= len(vary[v])
            
        self.analysis_var={'peak_delta':0,'baseline':0,'dvdt_threshold':0, 'peak_threshold':0}


    def _rem_key(self, d, key):
        r = dict(d)
        del r[key]
        return r


    def _run_instance(self, ** kwargs):

        print_v('============================================================= \n\n'+
                '     Instance (%s/%s): %s\n' % (self.complete+1, self.total_todo, kwargs))

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
                
                self.report['Simulations'][ref_here] = OrderedDict()
                report_here = self.report['Simulations'][ref_here]
                
                report_here['parameters'] = all_params
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
                
                report_here['analysis'] = OrderedDict()
                for a in analysed:
                    ref,var = a.split(':')
                    if not ref in report_here['analysis']:
                        report_here['analysis'][ref] = OrderedDict()
                    report_here['analysis'][ref][var] = analysed[a]
                    
                #self.report[ref_here]['parameters']
                
                self.complete += 1
            

    def run(self):

        print_v("Running...")
        self._sweep(self.vary, self.fixed)
        self.runner.finish()
        
        return self.report
    
    
    def print_report(self):

        print_v('--- REPORT:')
        import json

        print_v(json.dumps(self.report, indent=4))    
    
    
    def plotLines(self, param, value, save_figure_to=None, logx=False,logy=False):
        
        all_pvals = OrderedDict()
        all_lines = OrderedDict()
        
        for ref, info in self.report['Simulations'].items():
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
        colors = []
        
        for ref in all_lines:
            xs.append(all_pvals[ref])
            ys.append(all_lines[ref])
            labels.append(ref)
            markers.append('o')
            
            pop_id = ref.split('[')[0] if '[' in ref else ref.split('/')[0]
            pop = self.runner.last_network.get_child(pop_id, 'populations')
            color = [float(c) for c in pop.properties['color'].split()]
            #print_v("This trace %s has population %s: %s, so color: %s"%(ref,pop_id,pop,color))
            colors.append(color)
        
        ax = pynml.generate_plot(xs,                  
                                 ys,           
                                 "Plot of %s vs %s"%(value, param),              
                                 xaxis = param,            
                                 yaxis = value,          
                                 labels = labels,       
                                 markers = markers,    
                                 colors = colors,  
                                 logx = logx,
                                 logy = logy,
                                 show_plot_already=False,
                                 save_figure_to=save_figure_to)     # Save figure
        
class NeuroMLliteRunner():
    
    
    def __init__(self, nmllite_sim, plot_all=False, heatmap_all=False, show_plot_already=False, simulator='jNeuroML'):
        
        self.plot_all = plot_all
        self.heatmap_all = heatmap_all
        self.show_plot_already = show_plot_already
        self.base_dir = os.path.dirname(os.path.realpath(nmllite_sim))
        self.sim = load_simulation_json(nmllite_sim)
        self.simulator = simulator
        
        if self.plot_all:
            #plt.figure()
            self.ax = pynml.generate_plot([],                    
                         [],                   # Add 2 sets of y values
                         "Some traces generated from %s"%nmllite_sim,                  # Title
                         labels = [],
                         xaxis = 'Time (ms)',            # x axis legend
                         yaxis = '',   # y axis legend
                         show_plot_already=False)     # Save figure
                         
        if self.heatmap_all:

            self.hm_fig, self.hm_ax = plt.subplots()
            self.all_info = []
        
    def run_once(self, ** kwargs):
        print_v('Running NeuroMLlite simulation...')
        
        self.last_network = load_network_json(self.base_dir+'/'+self.sim.network)
        
        for a in kwargs:
            if a in self.last_network.parameters:
                print_v('  Setting %s to %s in network...'%(a, kwargs[a]))
                self.last_network.parameters[a] = kwargs[a]
            elif a in self.sim.fields:
                print_v('  Setting %s to %s in simulator...'%(a, kwargs[a]))
                setattr(self.sim,a,kwargs[a])
            else:
                print_v('  Cannot set parameter %s to %s in network or simulator...'%(a, kwargs[a]))
        
        traces, events = generate_and_run(self.sim, 
                                          simulator=self.simulator, 
                                          network=self.last_network, 
                                          return_results=True,
                                          base_dir=self.base_dir)
                                          
        print_v("Returned traces: %s, events: %s"%(traces.keys(), events.keys()))
        
        if self.plot_all or self.heatmap_all:
            for y in traces.keys():
                if y!='t':
                    pop_id = y.split('[')[0] if '[' in y else y.split('/')[0]
                    pop = self.last_network.get_child(pop_id, 'populations')
                    if pop:
                        color = [float(c) for c in pop.properties['color'].split()]
                        #print_v("This trace %s has population %s: %s, so color: %s"%(y,pop_id,pop,color))
                    else:
                        #print_v("This trace %s has population %s: %s which has no color..."%(y,pop_id,pop))
                        color = [1,0,0]
                
                    if self.plot_all:
                        label = '%s (%s)'%(y, kwargs)
                        self.ax.plot(traces['t'],traces[y],label=label)
                    
                    if self.heatmap_all:
                        downscale = int(0.1/self.sim.dt)
                        d = [traces[y][i] for i in range(len(traces[y])) if i%downscale==0]
                        print_v('-- Trace %s downscaled by factor %i from %i to %i points for heatmap'%(y,downscale,len(traces[y]),len(d)))
                        self.all_info.append(d)
                    
        return traces, events 
                    
                    
    def finish(self):
        
        if self.heatmap_all:
            
            plot0 = self.hm_ax.pcolormesh(np.array(self.all_info))
            self.hm_fig.colorbar(plot0)
        
        if self.show_plot_already:
            plt.show()
        

if __name__ == '__main__':


    fixed = {'dt':0.025,'N':30}

    quick = False
    #quick=True


    vary = {'stim_amp':['%spA'%(i/10.0) for i in xrange(-10,20,2)]}
    vary = {'stim_amp':['%spA'%(i/10.0) for i in xrange(-10,20,5)]}
    vary = {'weightInput':[1,2,5,10]}
    vary = {'weightInput':[1,2,3,20]}
    vary = {'eta':['%sHz'%(i) for i in xrange(0,140,20)]}
    #vary = {'eta':['100Hz']}
    #vary = {'stim_amp':['1.5pA']}
    
    
    nmllr = NeuroMLliteRunner('../../examples/SimExample7.json',
                              plot_all=True, 
                              heatmap_all=True,
                              show_plot_already=False)

    if quick:
        pass

    ps = ParameterSweep(nmllr, vary, fixed)

    report = ps.run()
    ps.print_report()
    
    #  ps.plotLines('weightInput','average_last_1percent',save_figure_to='average_last_1percent.png')
    #ps.plotLines('weightInput','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
    ps.plotLines('eta','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
    
    import matplotlib.pyplot as plt
    
    plt.show()
    
    '''
    vary['i'] = [1,2,3]

    ps = ParameterSweep(vary,fixed)

    ps.run()'''