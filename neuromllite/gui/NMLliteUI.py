
from os.path import dirname, realpath
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgWidget

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

from neuromllite.utils import load_simulation_json, load_network_json
from pyneuroml.pynml import get_next_hex_color


    
    

class NMLliteUI(QWidget):
    
    default_vals = {}
    
    def get_value_entry(self, name, value, entry_map):
        
        entry = QLineEdit()
        entry_map[name] = entry
        entry.setText(str(value))
        
        return entry
    
    
        
    def __init__(self, nml_sim_file, parent=None):
        super(NMLliteUI, self).__init__(parent)
        
        print('Styles available: %s'%QStyleFactory.keys())
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        
        header_font = QFont()
        header_font.setBold(True)
        
        self.backup_colors = {} # to ensure consistent random colors for traces... 
        
        self.simulation = load_simulation_json(nml_sim_file)
        self.sim_base_dir = dirname(nml_sim_file)
        if len(self.sim_base_dir)==0:
            self.sim_base_dir = '.' 
        
        self.network = load_network_json('%s/%s'%(self.sim_base_dir,self.simulation.network))

        nameLabel = QLabel("NMLlite file: %s"%realpath(nml_sim_file))
        nameLabel.setFont(header_font)
        
        paramLayout = QGridLayout()
        topLayout = QGridLayout()
        midLayout = QGridLayout()
        
        self.tabs = QTabWidget()
        self.simTab = QWidget()
        self.graphTab= QWidget()
        self.matrixTab= QWidget()
        self.tabs.resize(300,200)
        
        # Add tabs
        self.tabs.addTab(self.simTab, "Simulation")
        
        self.simTabLayout = QGridLayout()
        self.simTab.setLayout(self.simTabLayout)
        
        self.plotTabs = QTabWidget()
        
        self.tracesTab = QWidget()
        self.plotTabs.addTab(self.tracesTab, "Traces")
        self.heatmapTab = QWidget()
        self.plotTabs.addTab(self.heatmapTab, "Heatmap")
        self.spikesTab = QWidget()
        self.plotTabs.addTab(self.spikesTab, "Spikes")
        
        self.simTabLayout.addWidget(self.plotTabs)
        
        
        self.tracesLayout = QGridLayout()
        self.tracesTab.setLayout(self.tracesLayout)
        
        self.heatmapLayout = QGridLayout()
        self.heatmapTab.setLayout(self.heatmapLayout)
        self.heatmapColorbar=None
        
        
        from matplotlib.figure import Figure
        
        self.tracesFigure = Figure()
        self.tracesCanvas = FigureCanvas(self.tracesFigure)
        self.tracesLayout.addWidget(self.tracesCanvas)
        
        self.heatmapFigure = Figure()
        self.heatmapCanvas = FigureCanvas(self.heatmapFigure)
        self.heatmapLayout.addWidget(self.heatmapCanvas)

        
        self.tabs.addTab(self.graphTab, "Graph")
        self.graphTabTopLayout = QGridLayout()
        self.graphTab.setLayout(self.graphTabTopLayout)
        
        self.graphTabOptionsLayout = QGridLayout()
        self.graphTabTopLayout.addLayout(self.graphTabOptionsLayout,0,0)
        
        
        self.graphTabOptionsLayout.addWidget(QLabel("Graph level:"), 0, 0)
        
        self.graphLevelComboBox = QComboBox(self)
        self.graphLevelComboBox.addItem('-3')
        self.graphLevelComboBox.addItem('-2')
        self.graphLevelComboBox.addItem('-1')
        self.graphLevelComboBox.addItem('0')
        self.graphLevelComboBox.addItem('1')
        self.graphLevelComboBox.addItem('2')
        self.graphLevelComboBox.addItem('3')
        self.graphLevelComboBox.addItem('4')
        self.graphLevelComboBox.addItem('5')
        self.graphLevelComboBox.addItem('6')
        self.graphLevelComboBox.setCurrentIndex(6)
        self.graphTabOptionsLayout.addWidget(self.graphLevelComboBox, 0, 1)
        self.graphLevelComboBox.currentIndexChanged.connect(self.showGraph)
        
        self.graphTypeComboBox = QComboBox(self)
        self.graphTypeComboBox.addItem('d - dot')
        self.graphTypeComboBox.addItem('c - circo')
        self.graphTypeComboBox.addItem('n - neato')
        self.graphTypeComboBox.addItem('f - fdp')
        self.graphTypeComboBox.setCurrentIndex(0)
        self.graphTabOptionsLayout.addWidget(QLabel("GraphViz engine:"), 0, 2)
        self.graphTabOptionsLayout.addWidget(self.graphTypeComboBox, 0, 3)
        self.graphTypeComboBox.currentIndexChanged.connect(self.showGraph)
        
        self.graphTabLayout = QGridLayout()
        self.graphTabTopLayout.addLayout(self.graphTabLayout,1,0)
        
        
        self.tabs.addTab(self.matrixTab, "Matrix")
        self.matrixTabLayout = QGridLayout()
        self.matrixTab.setLayout(self.matrixTabLayout)
        
        
        # Add tabs to widget
        midLayout.addWidget(self.tabs, 0, 0)
        mainLayout = QGridLayout()

        
        topLayout.addWidget(nameLabel, 0, 0)
        #topLayout.addWidget(self.nameLine, 0, 1)
        
        rows = 0
        
        
        l = QLabel("Network parameters")
        l.setFont(header_font)
        paramLayout.addWidget(l, rows, 0)
        
        self.param_entries = {}

        if self.network.parameters is not None and len(self.network.parameters)>0:
            for p in sorted(self.network.parameters.keys()):
                rows+=1
                pval = self.network.parameters[p]
                label = QLabel("%s"%p)
                paramLayout.addWidget(label, rows, 0)
                entry = self.get_value_entry(p, pval, self.param_entries)
                paramLayout.addWidget(entry, rows, 1)
                
                
        self.graphButton = QPushButton("Generate graph")
        self.graphButton.show()
        self.graphButton.clicked.connect(self.showGraph)
        
        rows+=1
        paramLayout.addWidget(self.graphButton, rows, 0)
                
        self.matrixButton = QPushButton("Generate matrix")
        self.matrixButton.show()
        self.matrixButton.clicked.connect(self.showMatrix)
        
        rows+=1
        paramLayout.addWidget(self.matrixButton, rows, 0)
                
        rows+=1
        l = QLabel("Simulation parameters")
        l.setFont(header_font)
        paramLayout.addWidget(l, rows, 0)

        self.sim_entries = {}
        svars = ['dt','duration','seed']

        for s in svars:
            rows+=1
            sval = self.simulation.__getattr__(s)
            if sval is not None:
                label = QLabel("%s"%s)
                paramLayout.addWidget(label, rows, 0)
                
                
                entry = self.get_value_entry(s, sval, self.sim_entries)
                paramLayout.addWidget(entry, rows, 1)

        rows+=1
        
        paramLayout.addWidget(QLabel("Simulator:"), rows, 0)
        
        self.simulatorComboBox = QComboBox(self)
        self.simulatorComboBox.addItem("jNeuroML")
        self.simulatorComboBox.addItem("jNeuroML_NEURON")
        
        paramLayout.addWidget(self.simulatorComboBox, rows, 1)
        
        
        rows+=1

        self.runButton = QPushButton("Run simulation")
        self.runButton.show()
        self.runButton.clicked.connect(self.runSimulation)
        
        rows+=1
        paramLayout.addWidget(self.runButton, rows, 0)
        
        
        
        mainLayout.addLayout(topLayout, 0,1)
        mainLayout.addLayout(paramLayout, 1,0)
        mainLayout.addLayout(midLayout, 1,1)
        
        #self.setLayout(paramLayout)
        self.setLayout(mainLayout)
        
        self.setWindowTitle("NeuroMLlite GUI")
 
    
    
    
    def showMatrix(self):
        print("Matrix button was clicked.")
        
        self.update_net_sim()
        self.tabs.setCurrentWidget(self.matrixTab)
        
        from neuromllite.MatrixHandler import MatrixHandler
        
        level = 2
        
        handler = MatrixHandler(level, nl_network=self.network)
        
        from neuromllite.NetworkGenerator import generate_network
        generate_network(self.network, handler, always_include_props=True, base_dir='.')
    
        print("Done with MatrixHandler...")
    
    
    def showGraph(self):
        print("Graph button was clicked.")
        
        self.update_net_sim()
        self.tabs.setCurrentWidget(self.graphTab)
        
        from neuromllite.GraphVizHandler import GraphVizHandler
        
        engine = str(self.graphTypeComboBox.currentText()).split(' - ')[1]
        level = int(self.graphLevelComboBox.currentText())
        
        format = 'svg'
        format = 'png'
        
        handler = GraphVizHandler(level, engine=engine, nl_network=self.network, output_format=format, view_on_render=False)
        
        from neuromllite.NetworkGenerator import generate_network
        generate_network(self.network, handler, always_include_props=True, base_dir='.')
    
        print("Done with GraphViz...")
        
        if format=='svg':
            genFile = '%s.gv.svg'%self.network.id

            svgWidget = QSvgWidget(genFile)
            svgWidget.resize(svgWidget.sizeHint())
            svgWidget.show()
            self.graphTabLayout.addWidget(svgWidget,0,0)
            
        elif format=='png':
            genFile = '%s.gv.png'%self.network.id

            label = QLabel()
            pixmap = QPixmap(genFile)
            pixmap = pixmap.scaledToWidth(min(pixmap.width(),800), Qt.SmoothTransformation)
            label.setPixmap(pixmap)
            #self.resize(pixmap.width(),pixmap.height())
            if self.graphTabLayout.count()>0:
                self.graphTabLayout.itemAt(0).widget().setParent(None)
            self.graphTabLayout.addWidget(label,0,0)
        
        
    def update_net_sim(self):
        
        for p in self.param_entries:
            v = self.param_entries[p].text()
            try:
                v = int(v) 
            except:       
                try:
                    v = float(v) 
                except:
                    pass # leave as string...
                
            print('Setting param %s to %s'%(p,v))
            self.network.parameters[p] = v
            
        print('All params: %s'%self.network.parameters)

        for s in self.sim_entries:
            v = float(self.sim_entries[s].text())
            print('Setting simulation variable %s to %s'%(s,v))
            self.simulation.__setattr__(s,v)
        
         
    
    def runSimulation(self):
        
        simulator = str(self.simulatorComboBox.currentText())
        print("Run button was clicked. Running simulation %s in %s with %s"%(self.simulation.id, self.sim_base_dir, simulator))

        self.tabs.setCurrentWidget(self.simTab)
        
        self.update_net_sim()

        from neuromllite.NetworkGenerator import generate_and_run
        #return
        traces, events = generate_and_run(self.simulation,
                         simulator=simulator,
                         network=self.network,
                         return_results=True,
                         base_dir=self.sim_base_dir)

        import matplotlib.pyplot as plt

        info = "Data from sim of %s%s" \
                                            % (self.simulation.id, ' (%s)' % simulator 
                                                          if simulator else '')

        #from pyneuroml.pynml import generate_plot

        xs = []
        ys = []
        labels = []
        colors = []
        
        pop_colors = {}
        
        for pop in self.network.populations:
            for prop in pop.properties:
                if prop == 'color':
                    rgb = pop.properties[prop].split()
                    color = '#'
                    for a in rgb:
                        color = color+'%02x'%int(float(a)*255)
                        pop_colors[pop.id] = color
                        
        colors_used = []
        heat_array = []
        
        for key in sorted(traces.keys()):

            if key != 't':
                heat_array.append(traces[key])
                pop_id = key.split('/')[0]
                if pop_id in pop_colors and not pop_colors[pop_id] in colors_used:
                    colors.append(pop_colors[pop_id])
                    colors_used.append(pop_colors[pop_id])
                else:
                    if key in self.backup_colors:
                        colors.append(self.backup_colors[key])
                    else:
                        c = get_next_hex_color()
                        colors.append(c)
                        self.backup_colors[key] = c
                        
                    
                xs.append(traces['t'])
                ys.append(traces[key])
                labels.append(key)

        ax = self.tracesFigure.add_subplot(111)
        
        ax.clear()
        for i in range(len(xs)):
            ax.plot(xs[i],ys[i],label=labels[i],linewidth=0.5,color=colors[i])
            
        ax.set_xlabel('Time (s)')

        self.tracesFigure.legend()
        self.tracesCanvas.draw()
        
        import matplotlib
        cm = matplotlib.cm.get_cmap('jet')
        
        ax_heatmap = self.heatmapFigure.add_subplot(111)
        ax_heatmap.clear()
        hm = ax_heatmap.pcolormesh(heat_array,cmap=cm)
        #cbar = ax_heatmap.colorbar(im)
        
        if self.heatmapColorbar==None:
            self.heatmapColorbar = self.heatmapFigure.colorbar(hm)
            self.heatmapColorbar.set_label('Firing rate')
        
        self.heatmapCanvas.draw()

        


        print('Done!')
    
 
'''
btn = Button(window, text="Click Me", command=clicked)
rows+=1
btn.grid(column=0, row=rows)


window.mainloop()
'''

def main():
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    
    nml_sim_file = sys.argv[1]

    nmlui = NMLliteUI(nml_sim_file)
    nmlui.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    
