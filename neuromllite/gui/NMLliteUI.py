
from os.path import dirname, realpath
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgWidget

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

from neuromllite.utils import load_simulation_json, load_network_json


class NMLliteUI(QWidget):
    
    def __init__(self, nml_sim_file, parent=None):
        super(NMLliteUI, self).__init__(parent)
        
        print('Styles availible: %s'%QStyleFactory.keys())
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        
        self.simulation = load_simulation_json(nml_sim_file)
        self.sim_base_dir = dirname(nml_sim_file)
        self.network = load_network_json('%s/%s'%(self.sim_base_dir,self.simulation.network))

        nameLabel = QLabel("NMLlite file:")
        
        self.nameLine = QLineEdit()
        self.nameLine.setText(nml_sim_file)
        self.nameLine.setReadOnly(True)

        paramLayout = QGridLayout()
        topLayout = QGridLayout()
        midLayout = QGridLayout()
        
        self.tabs = QTabWidget()
        self.simTab = QWidget()
        self.graphTab= QWidget()
        self.tabs.resize(300,200)
        
        # Add tabs
        self.tabs.addTab(self.simTab, "Simulation")
        self.simTabLayout = QGridLayout()
        self.simTab.setLayout(self.simTabLayout)
        
        from matplotlib.figure import Figure
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.simTabLayout.addWidget(self.canvas)

        
        self.tabs.addTab(self.graphTab, "Graph")
        self.graphTabLayout = QGridLayout()
        self.graphTab.setLayout(self.graphTabLayout)
        
        
        # Add tabs to widget
        midLayout.addWidget(self.tabs, 0, 0)
        mainLayout = QGridLayout()

        
        topLayout.addWidget(nameLabel, 0, 0)
        topLayout.addWidget(self.nameLine, 0, 1)
        rows = 0
        
        paramLayout.addWidget(QLabel("Simulation parameters"), rows, 0)

        self.sim_entries = {}
        svars = ['dt','duration','seed']

        for s in svars:
            rows+=1
            sval = self.simulation.__getattr__(s)
            if sval is not None:
                label = QLabel("%s"%s)
                paramLayout.addWidget(label, rows, 0)
                
                txt = QLineEdit()
                self.sim_entries[s] = txt
                txt.setText(str(sval))
                paramLayout.addWidget(txt, rows, 1)

        rows+=1
        paramLayout.addWidget(QLabel("Network parameters"), rows, 0)
        
        self.param_entries = {}

        if self.network.parameters is not None and len(self.network.parameters)>0:
            for p in sorted(self.network.parameters.keys()):
                rows+=1
                param = self.network.parameters[p]
                label = QLabel("%s"%p)
                paramLayout.addWidget(label, rows, 0)
                txt = QLineEdit()
                self.param_entries[p] = txt
                txt.setText(str(param))
                paramLayout.addWidget(txt, rows, 1)

        self.runButton = QPushButton("Run simulation")
        self.runButton.show()
        self.runButton.clicked.connect(self.runSimulation)
        
        rows+=1
        paramLayout.addWidget(self.runButton, rows, 0)
        
        self.graphButton = QPushButton("Show graph")
        self.graphButton.show()
        self.graphButton.clicked.connect(self.showGraph)
        
        rows+=1
        paramLayout.addWidget(self.graphButton, rows, 0)
        
        
        mainLayout.addLayout(topLayout, 0,1)
        mainLayout.addLayout(paramLayout, 1,0)
        mainLayout.addLayout(midLayout, 1,1)
        
        #self.setLayout(paramLayout)
        self.setLayout(mainLayout)
        
        self.setWindowTitle("NeuroMLlite GUI")
 
        self.simulator='jNeuroML'
    
    
    
    def showGraph(self):
        print("Graph button was clicked. Running simulation %s in %s"%(self.simulation.id, self.sim_base_dir))
        
        from neuromllite.GraphVizHandler import GraphVizHandler, engines
        
        engine = 'dot'
        level = 3
        
        self.update_net_sim()
        
        handler = GraphVizHandler(level, engine=engine, nl_network=self.network, output_format='svg')
        
        from neuromllite.NetworkGenerator import generate_network
        generate_network(self.network, handler, always_include_props=True, base_dir='.')
    
        print("Done with GraphViz...")
        
        self.tabs.setCurrentWidget(self.graphTab)
        svgWidget = QSvgWidget('%s.gv.svg'%self.network.id)
        #svgWidget.setGeometry(300,300,300,300)
        svgWidget.show()
        self.graphTabLayout.addWidget(svgWidget,0,0)
        
        
    def update_net_sim(self):
        for p in self.param_entries:
            v = float(self.param_entries[p].text())
            print('Setting param %s to %s'%(p,v))
            self.network.parameters[p] = v

        for s in self.sim_entries:
            v = float(self.sim_entries[s].text())
            print('Setting simulation variable %s to %s'%(s,v))
            self.simulation.__setattr__(s,v)
        
        
    
    def runSimulation(self):
        print("Run button was clicked. Running simulation %s in %s"%(self.simulation.id, self.sim_base_dir))

        self.tabs.setCurrentWidget(self.simTab)
        
        self.update_net_sim()

        from neuromllite.NetworkGenerator import generate_and_run
        #return
        traces, events = generate_and_run(self.simulation,
                         simulator=self.simulator,
                         network=self.network,
                         return_results=True,
                         base_dir=self.sim_base_dir)

        import matplotlib.pyplot as plt

        info = "Data from sim of %s%s" \
                                            % (self.simulation.id, ' (%s)' % self.simulator 
                                                          if self.simulator else '')

        #from pyneuroml.pynml import generate_plot

        xs = []
        ys = []
        labels = []

        for key in traces:

            if key != 't':
                xs.append(traces['t'])
                ys.append(traces[key])
                labels.append(key)

        ax = self.figure.add_subplot(111)
        
        ax.clear()
        for i in range(len(xs)):
            ax.plot(xs[i],ys[i],label=labels[i])

        self.canvas.draw()


        print('Done!')
    
 
'''
btn = Button(window, text="Click Me", command=clicked)
rows+=1
btn.grid(column=0, row=rows)


window.mainloop()
'''

if __name__ == '__main__':
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    
    nml_sim_file = sys.argv[1]

    nmlui = NMLliteUI(nml_sim_file)
    nmlui.show()

    sys.exit(app.exec_())
