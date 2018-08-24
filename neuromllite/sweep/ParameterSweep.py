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

import sys
import random
import time

'''


        Work in progress!!!
        
        
'''

'''
    Can be used to run multiple simulations across a range of parameters
'''
class ParameterSweep():
    
    def __init__(self, 
                 runner, 
                 vary, 
                 fixed={}, 
                 verbose=False,
                 num_parallel_runs=1,
                 plot_all=False, 
                 heatmap_all=False, 
                 show_plot_already=False, ):

        self.sim = load_simulation_json(runner.nmllite_sim)
        
        ps_id = 'ParamSweep_%s_%s'%(self.sim.id, time.ctime().replace(' ','_' ).replace(':','.' ))
        
        print_v("Initialising ParameterSweep %s with %s, %s (%i parallel runs)" % (ps_id, vary, fixed, num_parallel_runs))
        
        os.mkdir(ps_id)
        self.result_dir = os.path.abspath(ps_id)
        
        self.runner = runner
        self.fixed = fixed
        self.vary = vary
        self.verbose=verbose
        self.num_parallel_runs=num_parallel_runs
        
        self.plot_all = plot_all
        self.heatmap_all = heatmap_all
        self.show_plot_already = show_plot_already
        
        self.complete = 0
        self.total_todo = 1
        self.report = OrderedDict()
        self.report['Varied parameters'] = vary
        self.report['Fixed parameters'] = fixed
        self.report['Simulations'] = OrderedDict()
        for v in vary:
            self.total_todo *= len(vary[v])
            
        self.analysis_var={'peak_delta':0,'baseline':0,'dvdt_threshold':0, 'peak_threshold':0}
        
        if self.plot_all:
            self.ax = pynml.generate_plot([],                    
                         [],                   # Add 2 sets of y values
                         "Some traces generated from %s"%runner.nmllite_sim,                  # Title
                         labels = [],
                         xaxis = 'Time (ms)',            # x axis legend
                         yaxis = 'Membrane potential (mV)',   # y axis legend
                         show_plot_already=False)     # Save figure
                         
        if self.heatmap_all:

            self.hm_fig, self.hm_ax = plt.subplots()
            self.hm_x = None
            self.hm_y = []
            self.hm_z = []
        

    def _rem_key(self, d, key):
        r = dict(d)
        del r[key]
        return r
    

    def _sweep(self, v, f, reference=''):
            
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
                
            
    def _run_all(self):
        
        import pp
        ppservers = ()
        job_server = pp.Server(self.num_parallel_runs, ppservers=ppservers)
        print_v('\n  == Running %i jobs across %i local processes\n '%(self.total_todo,job_server.get_ncpus()))
        jobs = []
        job_refs = {}
        
        submitted = 0
        for ref in self.report['Simulations']:
            
            report_here = self.report['Simulations'][ref]
                
            params = report_here['parameters']
            print_v("---- Submitting %s: %s"%(ref,params))
            
            job_dir = os.path.join(self.result_dir, ref)
            os.mkdir(job_dir)
            
            vars = (self.runner,
                    submitted+1, 
                    self.total_todo,
                    job_dir,
                    params)
                    
            job = job_server.submit(run_instance, 
                                    args=vars,
                                    modules=('pyneuroml.pynml',
                                             'shutil',
                                             'neuroml',
                                             'neuromllite',
                                             'neuromllite.sweep.ParameterSweep',
                                             'neuromllite.utils'))
            jobs.append(job)
            job_refs[len(jobs)-1] = ref
                
            submitted+=1
            
        print_v("Submitted all jobs: %s"%job_refs)
        
        for job_i in range(len(jobs)):
            job = jobs[job_i]
            ref = job_refs[job_i]
            report_here = self.report['Simulations'][ref]
            params = report_here['parameters']
            
            print_v("Checking parallel job %i/%i (%s)"%(job_i,len(jobs),ref))
            traces, events = job()
            
            self.last_network_ran = None
            
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
            
            self.complete += 1
            
            if self.plot_all or self.heatmap_all:
                for y in traces.keys():
                    if y!='t':
                        pop_id = y.split('[')[0] if '[' in y else y.split('/')[0]
                        pop = None # self.last_network_ran.get_child(pop_id, 'populations')
                        if pop:
                            color = [float(c) for c in pop.properties['color'].split()]
                            #print_v("This trace %s has population %s: %s, so color: %s"%(y,pop_id,pop,color))
                        else:
                            #print_v("This trace %s has population %s: %s which has no color..."%(y,pop_id,pop))
                            color = [1,0,0]

                        if self.plot_all:
                            label = '%s (%s)'%(y, params)
                            self.ax.plot(traces['t'],[v*1000 for v in traces[y]],label=label)

                        if self.heatmap_all:
                            downscale = int(0.1/self.sim.dt)
                            d = [traces[y][i]*1000 for i in range(len(traces[y])) if i%downscale==0]
                            tt = [traces['t'][i]*1000 for i in range(len(traces['t'])) if i%downscale==0]
                            print_v('-- Trace %s downscaled by factor %i from %i to %i points for heatmap'%(y,downscale,len(traces[y]),len(d)))
                            
                            pval = get_value_in_si(params[params.keys()[0]])
                            if self.hm_x==None:
                                self.hm_x = tt
                            self.hm_y.append(pval)
                            self.hm_z.append(d)
                
        job_server.print_stats()
        job_server.destroy()
        print("-------------------------------------------")

        
    def run(self):

        print_v("Running...")
        self._sweep(self.vary, self.fixed)
        self._run_all()
        
        if self.heatmap_all:
            
            plot0 = self.hm_ax.pcolormesh(np.array(self.hm_x), 
                                          np.array(self.hm_y), 
                                          np.array(self.hm_z))
            
            plt.xlabel('Time (ms)')
            plt.ylabel('%s '%self.vary.keys()[0])
            plt.xlim([self.hm_x[0],self.hm_x[-1]])
            plt.ylim([self.hm_y[0],self.hm_y[-1]])
            title = 'Values of %s'%self.vary.keys()
            self.hm_fig.canvas.set_window_title(title)
            plt.title(title)
            #plt.axes().set_aspect('equal')

            cb1 = self.hm_fig.colorbar(plot0)
            cb1.set_label('Membrane potential (mV)')
        
        if self.show_plot_already:
            plt.show()
        
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
            if self.last_network_ran:
                pop = self.last_network_ran.get_child(pop_id, 'populations')
                color = [float(c) for c in pop.properties['color'].split()]
            else:
                color = [random.random(),random.random(),random.random()]
                pop = None
            print_v("This trace %s has population %s: %s, so color: %s"%(ref,pop_id,pop,color))
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
    


def run_instance(runner, i, total, job_dir, params):

    print('============================================================= \n\n'+
          '     Instance (%s of %s): %s\n' % (i, total, params))
    
    return runner.run_once(job_dir, ** params)


        
'''
    Loads a single NeuroMLlite simulation/network, allows instances of this to be generated in
    multiple supported simulators, potentially with some parameters changed, and can plot
    the activity of the cells in the simulations
'''
class NeuroMLliteRunner():
    
    def __init__(self, 
                 nmllite_sim, 
                 simulator='jNeuroML'):
        
        self.base_dir = os.path.dirname(os.path.realpath(nmllite_sim))
        self.nmllite_sim = nmllite_sim
        self.simulator = simulator
        
        
    '''
        Run a single instance of the simulation, changing the parameters specified
    '''
    def run_once(self, job_dir, ** kwargs):
        
        from neuromllite.utils import print_v
        from neuromllite.utils import load_simulation_json,load_network_json
        from neuromllite.NetworkGenerator import generate_and_run
        from pyneuroml.pynml import get_value_in_si
        
        print_v('Running NeuroMLlite simulation...')
        sim = load_simulation_json(self.nmllite_sim)
        import random
        sim.id = '%s_%s'%(sim.id,random.random())
        network = load_network_json(self.base_dir+'/'+sim.network)
        
        for a in kwargs:
            if a in network.parameters:
                print_v('  Setting %s to %s in network...'%(a, kwargs[a]))
                network.parameters[a] = kwargs[a]
            elif a in sim.fields:
                print_v('  Setting %s to %s in simulator...'%(a, kwargs[a]))
                setattr(sim,a,kwargs[a])
            else:
                print_v('  Cannot set parameter %s to %s in network or simulator...'%(a, kwargs[a]))
                
        traces, events = generate_and_run(sim, 
                                          simulator = self.simulator, 
                                          network = network, 
                                          return_results = True,
                                          base_dir = self.base_dir,
                                          target_dir = job_dir)
                                          
                                          
        print_v("Returned traces: %s, events: %s"%(traces.keys(), events.keys()))
        
        return traces, events
                    
        


if __name__ == '__main__':


    if '-2d' in sys.argv:
        fixed = {'dt':0.025}
        vary = {'stim_amp':['%spA'%(i) for i in xrange(-40,220,40)],
                'stim_del':['%sms'%(i) for i in xrange(10,40,10)]}
        vary = {'stim_amp':['%spA'%(i) for i in xrange(-80,160,1)]}
        
        nmllr = NeuroMLliteRunner('Sim_IClamp_HH.json')

        ps = ParameterSweep(nmllr, 
                            vary, 
                            fixed,
                            num_parallel_runs=1,
                                  plot_all=True, 
                                  heatmap_all=True,
                                  show_plot_already=False)

        report = ps.run()
        ps.print_report()

        #  ps.plotLines('weightInput','average_last_1percent',save_figure_to='average_last_1percent.png')
        #ps.plotLines('weightInput','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
        ps.plotLines('stim_amp','mean_spike_frequency',save_figure_to='mean_spike_frequency_hh.png')

        import matplotlib.pyplot as plt

        plt.show()

    elif '-hh' in sys.argv:
        fixed = {'dt':0.025}

        vary = {'stim_amp':['%spA'%(i) for i in xrange(-200,1500,10)]}
        vary = {'stim_amp':['%spA'%(i) for i in xrange(-200,1600,300)]}
        vary = {'stim_amp':['%spA'%(i) for i in xrange(-40,220,20)]}
        
        simulator='jNeuroML_NEURON'
        simulator='jNeuroML_NetPyNE'
        simulator='NetPyNE'
        simulator='jNeuroML'
        
        nmllr = NeuroMLliteRunner('Sim_HHTest.json',
                                  simulator=simulator)
                                  
        '''print(nmllr)  
        nmllr.run_once()
        
        pstr0 = pickle.dumps(nmllr)'''
        

        ps = ParameterSweep(nmllr, 
                            vary, 
                            fixed,
                            num_parallel_runs=18,
                            plot_all=True, 
                            heatmap_all=True,
                            show_plot_already=False)

        report = ps.run()
        ps.print_report()

        ps.plotLines('stim_amp','mean_spike_frequency',save_figure_to='mean_spike_frequency_hh.png')

        import matplotlib.pyplot as plt

        plt.show()
        
    else:
        fixed = {'dt':0.025,'N':10}

        quick = False
        #quick=True


        vary = {'stim_amp':['%spA'%(i/10.0) for i in xrange(-10,20,2)]}
        vary = {'stim_amp':['%spA'%(i/10.0) for i in xrange(-10,20,5)]}
        vary = {'weightInput':[1,2,5,10]}
        vary = {'weightInput':[1,2,3,20]}
        vary = {'eta':['%sHz'%(i) for i in xrange(0,260,20)]}
        #vary = {'eta':['100Hz']}
        #vary = {'stim_amp':['1.5pA']}


        nmllr = NeuroMLliteRunner('../../examples/SimExample7.json')

        if quick:
            pass

        ps = ParameterSweep(nmllr, 
                            vary, 
                            fixed,
                            num_parallel_runs=16,
                                  plot_all=True, 
                                  heatmap_all=True,
                                  show_plot_already=False)

        report = ps.run()
        ps.print_report()

        #  ps.plotLines('weightInput','average_last_1percent',save_figure_to='average_last_1percent.png')
        #ps.plotLines('weightInput','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
        ps.plotLines('eta','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')

        import matplotlib.pyplot as plt

        plt.show()

