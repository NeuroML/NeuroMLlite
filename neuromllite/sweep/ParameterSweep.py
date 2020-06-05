import os

from neuromllite.utils import load_simulation_json
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
                 save_plot_all_to=None, 
                 heatmap_all=False, 
                 save_heatmap_to=None, 
                 heatmap_lims=None,
                 show_plot_already=False, 
                 peak_threshold = 0):

        self.sim = load_simulation_json(runner.nmllite_sim)
        
        self.colormap = 'jet'
        
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
        self.save_plot_all_to = save_plot_all_to
        self.heatmap_all = heatmap_all
        self.save_heatmap_to = save_heatmap_to
        self.heatmap_lims = heatmap_lims
        self.show_plot_already = show_plot_already
        
        self.index = 0
        self.total_todo = 1
        self.report = OrderedDict()
        self.report['Varied parameters'] = vary
        self.report['Fixed parameters'] = fixed
        self.report['Simulations'] = OrderedDict()
        for v in vary:
            self.total_todo *= len(vary[v])
            
        self.analysis_var={'peak_delta':0,'baseline':0,'dvdt_threshold':0, 'peak_threshold':peak_threshold}
        
        if self.plot_all:
            self.ax = pynml.generate_plot([],                    
                         [],                   # Add 2 sets of y values
                         "Traces generated from %s"%self.sim.id,                  # Title
                         labels = [],
                         xaxis = 'Time (ms)',            # x axis legend
                         yaxis = 'Membrane potential (mV)',   # y axis legend
                         title_above_plot = True,
                         show_plot_already=False)     # Save figure
                         
        if self.heatmap_all:
            if len(self.vary)!=1:
                raise Exception('Heatmap can only be used when only one parameter is varied...')
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

                self._sweep(others, all_params, reference='%s_%s%s' % (reference, keys[0], (str(val)).replace('-','min')))

        else:
            vals = v[keys[0]]
            for val in vals:
                all_params = dict(f)
                all_params[keys[0]] = val
                r = '%s_%s%s' % (reference, keys[0], (str(val)).replace('-','min'))
                ref_here = 'RUN%s_%s_%s' % (self.index, self.sim.id, r)
                self.index+=1
                all_params['reference'] = ref_here
                
                self.report['Simulations'][ref_here] = OrderedDict()
                report_here = self.report['Simulations'][ref_here]
                
                report_here['parameters'] = all_params
                
                
    def _get_sim_duration_ms(self,parameters):
        if 'duration' in parameters:
            return parameters['duration']
        else:
            return self.sim.duration
            
            
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
            report_here['analysis'] = OrderedDict()
            params = report_here['parameters']
            
            print_v("Checking parallel job %i/%i (%s)"%(job_i,len(jobs),ref))
            traces, events = job()
            
            self.last_network_ran = None
            
            if len(traces)>0:
                times = [t*1000. for t in traces['t']]
                volts = OrderedDict()
                for tr in traces:
                    if tr.endswith('/v'): volts[tr] = [v*1000. for v in traces[tr]]
                    if tr.endswith('/r'): volts[tr] = [r for r in traces[tr]]
                    if tr.endswith('/V'): volts[tr] = [V for V in traces[tr]]
                    
                print_v("Analysing %s..."%traces.keys())

                analysis_data=analysis.NetworkAnalysis(volts,
                                                   times,
                                                   self.analysis_var,
                                                   start_analysis=0,
                                                   end_analysis=times[-1],
                                                   smooth_data=False,
                                                   show_smoothed_data=False,
                                                   verbose=self.verbose)

                analysed = analysis_data.analyse()

                for a in sorted(analysed.keys()):
                    ref0,var = a.split(':')
                    if not ref0 in report_here['analysis']:
                        report_here['analysis'][ref0] = OrderedDict()
                    report_here['analysis'][ref0][var] = analysed[a]
                
            for e in sorted(events.keys()):
                x = events[e]
                print_v('Examining event %s: %s -> %s (len: %i)'%(e, x[0] if len(x)>0 else '-',x[-1] if len(x)>0 else '-',len(x)))
                ref0 = '%s/spike'%e
                analysed = OrderedDict()
                l = len(x)
                tmax_si = self._get_sim_duration_ms(params)/1000.
                f_hz = l / tmax_si
                #print_v('This has %s points in %s sec, so %s Hz'%(l,tmax_si, f_hz))
                analysed["mean_spike_frequency"] = f_hz
                
                if not ref0 in report_here['analysis']:
                    report_here['analysis'][ref0] = OrderedDict()
                    
                report_here['analysis'][ref0] = analysed
                
            
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
                            self.ax.plot([t*1000 for t in traces['t']],[v*1000 for v in traces[y]],label=label)

                        if self.heatmap_all:
                            dt = self.sim.dt if not 'dt' in params else params['dt']
                            downscale = int(0.1/dt)
                            d = [traces[y][i]*1000 for i in range(len(traces[y])) if i%downscale==0]
                            tt = [traces['t'][i]*1000 for i in range(len(traces['t'])) if i%downscale==0]
                            
                            param_name = self.vary.keys()[0]
                            pval = get_value_in_si(params[param_name])
                            if self.hm_x==None:
                                self.hm_x = tt
                            print_v('  ==  Trace %s (%s) downscaled by factor %i from %i to %i points for heatmap; y value: %s=%s'%(y,ref,downscale,len(traces[y]),len(d), param_name, pval))
                            self.hm_y.append(pval)
                            self.hm_z.append(d)
                            
            print_v("Finished checking parallel job %i/%i (%s)"%(job_i,len(jobs),ref))
                
        job_server.print_stats()
        job_server.destroy()
        print_v("-------------------------------------------")

        
    def run(self):

        print_v("Running...")
        self._sweep(self.vary, self.fixed)
        self._run_all()
        
        if self.plot_all and self.save_plot_all_to:
            print_v("Saving image to %s of plot"%(os.path.abspath(self.save_plot_all_to)))
            plt.savefig(self.save_plot_all_to,bbox_inches='tight')
        
        if self.heatmap_all:
            
            self.hm_fig, self.hm_ax = plt.subplots()
            z = np.array(self.hm_z)
            
            print_v('Plotting x: %s->%s (%i), y: %s->%s (%i), z: %s->%s (%i)' % \
                                       (self.hm_x[0], self.hm_x[-1], len(self.hm_x),
                                       self.hm_y[0], self.hm_y[-1], len(self.hm_y),
                                       z.min(), z.max(), z.size))
                                       
            #yvals = [i for i in range(len(self.hm_y))]
            #yvals = np.array(self.hm_y)
            
            if not self.heatmap_lims:                         
                plot0 = self.hm_ax.pcolormesh(np.array(self.hm_x), 
                                              np.array(self.hm_y), 
                                              z,
                                              cmap=self.colormap)
            else:  
                plot0 = self.hm_ax.pcolormesh(np.array(self.hm_x), 
                                              np.array(self.hm_y), 
                                              z,
                                              vmin=self.heatmap_lims[0],
                                              vmax=self.heatmap_lims[1],
                                              cmap=self.colormap)
                
            #plt.set_yticks(np.arange(a_n_.shape[0]) + 0.5, minor=False)
            #self.hm_ax.set_yticklabels(['ff%s'%i for i in range(len(self.hm_y))])
            
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

            if self.save_heatmap_to:
                print_v("Saving image to %s of plot"%(os.path.abspath(self.save_heatmap_to)))
                plt.savefig(self.save_heatmap_to,bbox_inches='tight')
            
        
        if self.show_plot_already:
            plt.show()
        
        return self.report
    
    
    def print_report(self):

        print_v('--- REPORT:')
        import json
        print_v(json.dumps(self.report, indent=4))    
    
    
    def plotLines(self, first_param, value, second_param=None, save_figure_to=None, logx=False,logy=False):
        
        all_pvals = OrderedDict()
        all_lines = OrderedDict()
        
        all_traces = []
        
        DEFAULT_TRACE = self.sim.id
        if not second_param:
            all_traces = [DEFAULT_TRACE]
        else:
            for ref, info in self.report['Simulations'].items():
                val2 = get_value_in_si(info['parameters'][second_param])
                trace_id = '%s__%s'%(second_param,val2)
                trace_id = val2
                if not trace_id in all_traces:
                    all_traces.append(trace_id)
            
        for t in all_traces:
            all_lines[t] = {}
            all_pvals[t] = {}
            
        
        for ref, info in self.report['Simulations'].items():
            print_v('Checking %s: %s'%(ref,info['parameters']))
            
            pval = get_value_in_si(info['parameters'][first_param])
            
            if not second_param:
                trace_id = DEFAULT_TRACE
            else:
                val2 = get_value_in_si(info['parameters'][second_param])
                trace_id = val2
                
            if ':' in value:
                matching_ref = value.split(':')[0]
                feature = value.split(':')[1]
            else:
                matching_ref = '*'
                feature = value
                
            for cell_ref in info['analysis']:
                print_v('Checking if %s matches %s, feature: %s (from %s)'%(cell_ref, matching_ref, feature, value))
                if matching_ref==cell_ref or matching_ref=='*':
                    #print('y')
                    if not cell_ref in all_lines[trace_id]:
                        all_lines[trace_id][cell_ref] = []
                        all_pvals[trace_id][cell_ref] = []

                    vval = info['analysis'][cell_ref][feature]

                    all_lines[trace_id][cell_ref].append(vval)
                    all_pvals[trace_id][cell_ref].append(pval)
        
        
        print_v('Plot x: %s'%all_pvals)
        print_v('Plot y: %s'%all_lines)
        
        xs= []
        ys = []
        labels = []
        markers = []
        colors = []
        maxy = -1 * sys.float_info.max
        
        for t in all_traces:
        
            for ref in all_lines[t]:
                print_v('Add data %s, %s'%(t,ref))
                
                xs.append(all_pvals[t][ref])
                ys.append(all_lines[t][ref])

                maxy = max(maxy, max(all_lines[t][ref]))

                labels.append('%s - %s'%(t,ref))
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

        xlim = None
        ylim = None
            
        yaxis = value.replace('_', ' ')
        yaxis = yaxis[0].upper()+yaxis[1:]
        
        if value=='mean_spike_frequency':
            yaxis += ' (Hz)'
            ylim = [maxy*-0.1,maxy*1.1]
            print_v('Setting y axes on freq plot to: %s'% ylim)
            
        
        ax = pynml.generate_plot(xs,                  
                                 ys,           
                                 "Plot of %s vs %s in %s"%(value, first_param, self.sim),              
                                 xaxis = first_param,            
                                 yaxis = yaxis,          
                                 labels = labels if len(labels)>1 else None,       
                                 markers = markers,    
                                 colors = colors,  
                                 xlim = xlim,
                                 ylim = ylim,
                                 logx = logx,
                                 logy = logy,
                                 show_plot_already=False,
                                 legend_position='right',
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
                     
        real_sim = os.path.realpath(nmllite_sim)
        print_v('Created NeuroMLliteRunner to run %s in %s'%(real_sim, simulator))
        
        self.base_dir = os.path.dirname(real_sim)
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
        
        print_v('Running NeuroMLlite simulation in dir: %s...'%job_dir)
        sim = load_simulation_json(self.nmllite_sim)
        import random
        sim.id = '%s%s'%(sim.id, '_%s'%kwargs['reference'] if 'reference' in kwargs else '')
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
                
        vary = {'stim_amp':['%spA'%(i) for i in [-50,100]],
                'stim_del':['%sms'%(i) for i in [10,20]]}
                
        vary = {'stim_amp':['%spA'%(i) for i in xrange(-40,220,20)],
                'stim_del':['%sms'%(i) for i in [10,20]]}
        
        simulator='jNeuroML_NEURON'
        simulator='jNeuroML'
        
        nmllr = NeuroMLliteRunner('Sim_HHTest.json', 
                                  simulator=simulator)

        ps = ParameterSweep(nmllr, 
                            vary, 
                            fixed,
                            num_parallel_runs=6,
                            plot_all=True, 
                            heatmap_all=False,
                            show_plot_already=False)

        report = ps.run()
        ps.print_report()

        #  ps.plotLines('weightInput','average_last_1percent',save_figure_to='average_last_1percent.png')
        #ps.plotLines('weightInput','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
        ps.plotLines('stim_amp',
                     value='pop_hhcell[0]/v:mean_spike_frequency',
                     second_param='stim_del',
                     save_figure_to='mean_spike_frequency_hh.png')
        '''
        ps.plotLines('stim_amp',
                     value='pop_hhcell[0]/v:first_spike_time',
                     second_param='stim_del',
                     save_figure_to='first_spike_time_hh.png')'''
        ps.plotLines('stim_amp',
                     value='pop_hhcell[0]/v:maximum',
                     second_param='stim_del',
                     save_figure_to='maximum_hh.png')
                     

        import matplotlib.pyplot as plt

        plt.show()

    elif '-hh' in sys.argv:
        fixed = {'dt':0.025}

        vary = {'stim_amp':['%spA'%(i) for i in xrange(-200,1500,10)]}
        vary = {'stim_amp':['%spA'%(i) for i in xrange(-100,1800,20)]}
        #vary = {'stim_amp':['%spA'%(i) for i in xrange(-100,500,5)]}
        
        simulator='jNeuroML_NetPyNE'
        simulator='NetPyNE'
        simulator='jNeuroML_NEURON'
        simulator='jNeuroML'
        
        nmllr = NeuroMLliteRunner('Sim_HHTest.json',
                                  simulator=simulator)        

        ps = ParameterSweep(nmllr, 
                            vary, 
                            fixed,
                            num_parallel_runs=6,
                            plot_all=True, 
                            heatmap_all=True,
                            heatmap_lims=[-100,20],
                            show_plot_already=False)

        report = ps.run()
        ps.print_report()

        ps.plotLines('stim_amp','mean_spike_frequency',save_figure_to='mean_spike_frequency_hh.png')

        import matplotlib.pyplot as plt

        plt.show()

    elif '-dt' in sys.argv:
        fixed = {'stim_amp':'500pA'}

        vary = {'dt':[0.025,0.02,0.015,0.01,0.005,0.0025]}
        vary = {'dt':[0.1,0.05,0.025,0.01,0.005,0.0025,0.001]}
        
        simulator='jNeuroML_NetPyNE'
        simulator='NetPyNE'
        simulator='jNeuroML'
        simulator='jNeuroML_NEURON'
        
        nmllr = NeuroMLliteRunner('Sim_HHTest.json',
                                  simulator=simulator)        

        ps = ParameterSweep(nmllr, 
                            vary, 
                            fixed,
                            num_parallel_runs=6,
                            save_plot_all_to='dt_traces_hh.png',
                            heatmap_all=True,
                            save_heatmap_to='heatmap_dt_hh.png',
                            plot_all=True, 
                            show_plot_already=False)

        report = ps.run()
        ps.print_report()

        ps.plotLines('dt','mean_spike_frequency',save_figure_to='mean_spike_frequency_dt_hh.png', logx=True)

        import matplotlib.pyplot as plt

        plt.show()
        
    elif '-run' in sys.argv: 
        
        simulator = 'jNeuroML_NetPyNE'
        simulator = 'jNeuroML'
        #simulator = 'PyNN_NEST'
        nmllr = NeuroMLliteRunner('../../examples/SimExample7.json',
                                  simulator=simulator)
        
        traces, events = nmllr.run_once('.', reference='ref0')
        
    elif '-hr' in sys.argv:
        fixed = {'dt':25}

        quick = False
        #quick=True

        vary = {'c':[-3,-1, 1, 3]}
        #vary = {'a':[.8,1,1.2]}
        #vary = {'eta':['100Hz']}
        #vary = {'stim_amp':['1.5pA']}


        simulator = 'jNeuroML'
        simulator='jNeuroML_NEURON'
        nmllr = NeuroMLliteRunner('../../examples/SimExample9.json', simulator=simulator)

        if quick:
            pass

        ps = ParameterSweep(nmllr, 
                            vary, 
                            fixed,
                            num_parallel_runs=6,
                                  plot_all=True, 
                                  heatmap_all=False,
                                  show_plot_already=False)

        report = ps.run()
        ps.print_report()
        
        #for k in vary:
        #    ps.plotLines(k,'mean_spike_frequency',save_figure_to='mean_spike_frequency_dt_hh.png', logx=True)

        #  ps.plotLines('weightInput','average_last_1percent',save_figure_to='average_last_1percent.png')
        #ps.plotLines('weightInput','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
        #ps.plotLines('eta','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')

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
        vary = {'eta':[i/100. for i in xrange(0,200,20)]}
        #vary = {'eta':['100Hz']}
        #vary = {'stim_amp':['1.5pA']}


        nmllr = NeuroMLliteRunner('../../examples/SimExample7.json')

        if quick:
            pass

        ps = ParameterSweep(nmllr, 
                            vary, 
                            fixed,
                            num_parallel_runs=6,
                                  plot_all=False, 
                                  heatmap_all=False,
                                  show_plot_already=False)

        report = ps.run()
        ps.print_report()

        #  ps.plotLines('weightInput','average_last_1percent',save_figure_to='average_last_1percent.png')
        #ps.plotLines('weightInput','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')
        ps.plotLines('eta','mean_spike_frequency',save_figure_to='mean_spike_frequency.png')

        import matplotlib.pyplot as plt

        plt.show()

