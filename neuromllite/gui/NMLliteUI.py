
from tkinter import *
from os.path import dirname, realpath
import sys
 
window = Tk()
 
window.title("NeuroMLlite GUI")

f = sys.argv[1]

from neuromllite.utils import load_simulation_json, load_network_json

sim = load_simulation_json(f)
sim_base_dir = dirname(f)
network = load_network_json('%s/%s'%(sim_base_dir,sim.network))

print sim



lbl = Label(window, text="File loaded: %s"%f)

rows = 0
lbl.grid(column=0, row=rows)

rows+=1

sim_entries = {}
svars = ['dt','duration','seed']

for s in svars:
    rows+=1
    sval = sim.__getattr__(s)
    lbl = Label(window, text="%s"%s)
    lbl.grid(column=0, row=rows)
    txt = Entry(window, width=10)
    sim_entries[s] = txt
    txt.insert(END,sval)
    txt.grid(column=1, row=rows)
    

param_entries = {}

for p in network.parameters:
    rows+=1
    param = network.parameters[p]
    lbl = Label(window, text="%s"%p)
    lbl.grid(column=0, row=rows)
    txt = Entry(window, width=10)
    param_entries[p] = txt
    txt.insert(END,param)
    txt.grid(column=1, row=rows)
 
#window.geometry('350x200')

simulator='jNeuroML'
def clicked():
    print("Button was clicked. Running simulation %s in %s"%(sim.id, sim_base_dir))
    
    for p in param_entries:
        v = float(param_entries[p].get())
        print('Setting param %s to %s'%(p,v))
        network.parameters[p] = v
        
    for s in sim_entries:
        v = float(sim_entries[s].get())
        print('Setting simulation variable %s to %s'%(s,v))
        sim.__setattr__(s,v)
    
    from neuromllite.NetworkGenerator import generate_and_run
    #return
    traces, events = generate_and_run(sim,
                     simulator=simulator,
                     network=network,
                     return_results=True,
                     base_dir=sim_base_dir)
    
    import matplotlib.pyplot as plt
    
    info = "Data from sim of %s%s" \
                                        % (f, ' (%s)' % simulator 
                                                      if simulator else '')
                                                      
    from pyneuroml.pynml import generate_plot
            
    xs = []
    ys = []
    labels = []
    


    for key in traces:

        if key != 't':
            xs.append(traces['t'])
            ys.append(traces[key])
            labels.append(key)

    generate_plot(xs,ys,'Results',labels=labels)



    print('Done!')
    
 

btn = Button(window, text="Click Me", command=clicked)
rows+=1
btn.grid(column=0, row=rows)


window.mainloop()