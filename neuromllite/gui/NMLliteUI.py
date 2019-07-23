from os.path import dirname
from os.path import realpath
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import *

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

import matplotlib
from matplotlib.figure import Figure

from neuromllite.utils import load_network_json
from neuromllite.utils import load_simulation_json
from neuromllite.utils import evaluate
from pyneuroml.pynml import get_next_hex_color


class NMLliteUI(QWidget):
    
    default_vals = {}
    
    simulators = ['jNeuroML',
        'jNeuroML_NEURON',
        'jNeuroML_NetPyNE',
        'PyNN_NEURON',
        'PyNN_NEST']
    
    
    def updated_param(self, p):
        """A parameter has been updated"""
        
        print('=====   Param %s changed' % p)
        
        if self.autoRunCheckBox.isChecked():
            self.runSimulation()
        else:
            print('Nothing changing...')
        
        
    def get_value_entry(self, name, value, entry_map):
        """Create a graphical element for displaying/setting values"""
        simple = False
        simple = True
        
        if simple:
            entry = QLineEdit()
            entry_map[name] = entry
            entry.setText(str(value))

        else:
        
            try:
                entry = QDoubleSpinBox()
                entry_map[name] = entry
                entry.setMaximum(1e6)
                entry.setMinimum(-1e6)
                entry.setSingleStep(value / 20.0)
                entry.setValue(float(value))
                '''
                print 555
                print entry.maximum()
                print entry.minimum()
                print entry.singleStep()
                print entry.text()
                '''
                
                entry.valueChanged.connect(self.updated_param)
                
            except Exception as e:
                print e
                
                entry = QLineEdit()
                entry_map[name] = entry
                entry.setText(str(value))
                entry.textChanged.connect(self.updated_param)
        
        '''print('Created value entry widget for %s (= %s): %s (%s)' % \
              (name, value, entry, entry.text()))'''
        return entry
    
    
    def __init__(self, nml_sim_file, parent=None):
        """Constructor for the GUI"""
        
        super(NMLliteUI, self).__init__(parent)
        
        
        #print('Styles available: %s'%QStyleFactory.keys())
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        
        header_font = QFont()
        header_font.setBold(True)
        
        self.backup_colors = {} # to ensure consistent random colors for traces... 
        
        self.simulation = load_simulation_json(nml_sim_file)
        self.sim_base_dir = dirname(nml_sim_file)
        if len(self.sim_base_dir) == 0:
            self.sim_base_dir = '.' 
        
        self.network = load_network_json('%s/%s' % (self.sim_base_dir, self.simulation.network))

        nameLabel = QLabel("NMLlite file: %s" % realpath(nml_sim_file))
        nameLabel.setFont(header_font)
        
        paramLayout = QGridLayout()
        topLayout = QGridLayout()
        midLayout = QGridLayout()
        
        self.tabs = QTabWidget()
        self.simTab = QWidget()
        self.graphTab = QWidget()
        self.matrixTab = QWidget()
        self.tabs.resize(300, 200)
        
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
        
        self.tracesTabTopLayout = QGridLayout()
        self.tracesTab.setLayout(self.tracesTabTopLayout)
        
        self.tracesTabOptionsLayout = QGridLayout()
        self.tracesTabTopLayout.addLayout(self.tracesTabOptionsLayout, 0, 0)
        
        self.showTracesLegend = QCheckBox("Legend")
        self.tracesTabOptionsLayout.addWidget(self.showTracesLegend, 0, 0)
        
        self.tracesTabLayout = QGridLayout()
        self.tracesTabTopLayout.addLayout(self.tracesTabLayout, 1, 0)
        
        self.heatmapLayout = QGridLayout()
        self.heatmapTab.setLayout(self.heatmapLayout)
        self.heatmapColorbar = None
        
        self.tracesFigure = Figure()
        self.tracesCanvas = FigureCanvas(self.tracesFigure)
        self.tracesTabLayout.addWidget(self.tracesCanvas)
        
        self.heatmapFigure = Figure()
        self.heatmapCanvas = FigureCanvas(self.heatmapFigure)
        self.heatmapLayout.addWidget(self.heatmapCanvas)
        
        self.spikesLayout = QGridLayout()
        self.spikesTab.setLayout(self.spikesLayout)
        self.spikesFigure = Figure()
        self.spikesCanvas = FigureCanvas(self.spikesFigure)
        self.spikesLayout.addWidget(self.spikesCanvas)

        
        self.tabs.addTab(self.graphTab, "Graph")
        self.graphTabTopLayout = QGridLayout()
        self.graphTab.setLayout(self.graphTabTopLayout)
        
        self.graphTabOptionsLayout = QGridLayout()
        self.graphTabTopLayout.addLayout(self.graphTabOptionsLayout, 0, 0)
        
        
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
        self.graphTabTopLayout.addLayout(self.graphTabLayout, 1, 0)
        
        
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

        if self.network.parameters is not None and len(self.network.parameters) > 0:
            for p in sorted(self.network.parameters.keys()):
                rows += 1
                pval = self.network.parameters[p]
                label = QLabel("%s" % p)
                paramLayout.addWidget(label, rows, 0)
                entry = self.get_value_entry(p, pval, self.param_entries)
                paramLayout.addWidget(entry, rows, 1)
                
                
        self.graphButton = QPushButton("Generate graph")
        self.graphButton.show()
        self.graphButton.clicked.connect(self.showGraph)
        
        rows += 1
        paramLayout.addWidget(self.graphButton, rows, 0)
                
        self.matrixButton = QPushButton("Generate matrix")
        self.matrixButton.show()
        self.matrixButton.clicked.connect(self.showMatrix)
        
        rows += 1
        paramLayout.addWidget(self.matrixButton, rows, 0)
                
        rows += 1
        l = QLabel("Simulation parameters")
        l.setFont(header_font)
        paramLayout.addWidget(l, rows, 0)

        self.sim_entries = {}
        svars = ['dt', 'duration', 'seed']

        for s in svars:
            rows += 1
            sval = self.simulation.__getattr__(s)
            if sval is not None:
                label = QLabel("%s" % s)
                paramLayout.addWidget(label, rows, 0)
                
                
                entry = self.get_value_entry(s, sval, self.sim_entries)
                paramLayout.addWidget(entry, rows, 1)

        rows += 1
        
        paramLayout.addWidget(QLabel("Simulator:"), rows, 0)
        
        self.simulatorComboBox = QComboBox(self)
        for sim in self.simulators:
            self.simulatorComboBox.addItem(sim)
        
        paramLayout.addWidget(self.simulatorComboBox, rows, 1)
        rows += 1

        self.runButton = QPushButton("Run simulation")
        self.runButton.show()
        self.runButton.clicked.connect(self.runSimulation)
        
        self.autoRunCheckBox = QCheckBox("Auto run")
        rows += 1
        paramLayout.addWidget(self.runButton, rows, 0)
        paramLayout.addWidget(self.autoRunCheckBox, rows, 1)
        
        
        mainLayout.addLayout(topLayout, 0, 1)
        mainLayout.addLayout(paramLayout, 1, 0)
        mainLayout.addLayout(midLayout, 1, 1)
        
        #self.setLayout(paramLayout)
        self.setLayout(mainLayout)
        
        self.setWindowTitle("NeuroMLlite GUI")
 
    
    def showMatrix(self):
        """Generate matrix buttom has been pressed"""
        
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
        """Generate graph buttom has been pressed"""
        
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
        
        if format == 'svg':
            genFile = '%s.gv.svg' % self.network.id

            svgWidget = QSvgWidget(genFile)
            svgWidget.resize(svgWidget.sizeHint())
            svgWidget.show()
            self.graphTabLayout.addWidget(svgWidget, 0, 0)
            
        elif format == 'png':
            genFile = '%s.gv.png' % self.network.id

            label = QLabel()
            pixmap = QPixmap(genFile)
            pixmap = pixmap.scaledToWidth(min(pixmap.width(), 800), Qt.SmoothTransformation)
            label.setPixmap(pixmap)
            #self.resize(pixmap.width(),pixmap.height())
            if self.graphTabLayout.count() > 0:
                self.graphTabLayout.itemAt(0).widget().setParent(None)
            self.graphTabLayout.addWidget(label, 0, 0)
        
        
    def update_net_sim(self):
        """Set the parameters in the network/simulation from the GUI values"""
        
        for p in self.param_entries:
            v = self.param_entries[p].text()
            try:
                v = int(v) 
            except:       
                try:
                    v = float(v) 
                except:
                    pass # leave as string...
                
            print('Setting param %s to %s' % (p, v))
            self.network.parameters[p] = v
            
        print('All params: %s' % self.network.parameters)

        for s in self.sim_entries:
            v = float(self.sim_entries[s].text())
            print('Setting simulation variable %s to %s' % (s, v))
            self.simulation.__setattr__(s, v)
        
         
    def runSimulation(self):
        """Run a simulation in the chosen simulator"""
        
        simulator = str(self.simulatorComboBox.currentText())
        print("Run button was clicked. Running simulation %s in %s with %s" % (self.simulation.id, self.sim_base_dir, simulator))

        self.tabs.setCurrentWidget(self.simTab)
        
        self.update_net_sim()
        

        from neuromllite.NetworkGenerator import generate_and_run
        #return
        self.current_traces, self.current_events = generate_and_run(self.simulation,
                                          simulator=simulator,
                                          network=self.network,
                                          return_results=True,
                                          base_dir=self.sim_base_dir)
                                          
        self.replotSimResults()
        

    def replotSimResults(self):
        
        simulator = str(self.simulatorComboBox.currentText())

        info = "Data from sim of %s%s" \
            % (self.simulation.id, ' (%s)' % simulator 
               if simulator else '')
               
        pop_colors = {}
        
        for pop in self.network.populations:
            for prop in pop.properties:
                if prop == 'color':
                    rgb = pop.properties[prop].split()
                    color = '#'
                    for a in rgb:
                        color = color + '%02x' % int(float(a) * 255)
                        pop_colors[pop.id] = color

        ## Plot traces
        
        xs = []
        ys = []
        labels = []
        colors = []
        
                        
        colors_used = []
        heat_array = []
        
        for key in sorted(self.current_traces.keys()):

            if key != 't':
                heat_array.append(self.current_traces[key])
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
                        
                    
                xs.append(self.current_traces['t'])
                ys.append(self.current_traces[key])
                labels.append(key)

        ax_traces = self.tracesFigure.add_subplot(111)
        
        ax_traces.clear()
        for i in range(len(xs)):
            ax_traces.plot(xs[i], ys[i], label=labels[i], linewidth=0.5, color=colors[i])
            
        ax_traces.set_xlabel('Time (s)')

        if self.showTracesLegend.isChecked():
            self.tracesFigure.legend()
        self.tracesCanvas.draw()
        
        
        ## Plot heatmap
        
        ax_heatmap = self.heatmapFigure.add_subplot(111)
        ax_heatmap.clear()
        
        cm = matplotlib.cm.get_cmap('jet')
        hm = ax_heatmap.pcolormesh(heat_array, cmap=cm)
        #cbar = ax_heatmap.colorbar(im)
        
        if self.heatmapColorbar == None:
            self.heatmapColorbar = self.heatmapFigure.colorbar(hm)
            self.heatmapColorbar.set_label('Firing rate')
        
        self.heatmapCanvas.draw()
        
        
        ## Plot spikes
        
        ax_spikes = self.spikesFigure.add_subplot(111)
        ax_spikes.clear()
        
        ids_for_pop = {}
        ts_for_pop = {}
        
        for k in self.current_events.keys():
            spikes = self.current_events[k]
            print('%s: %s'%(k, len(spikes)))
            pop_id = k.split('/')[0]
            cell_id = int(k.split('/')[1])
            if not pop_id in ids_for_pop:
                ids_for_pop[pop_id] = []
                ts_for_pop[pop_id] = []
            
            for t in spikes:
                ids_for_pop[pop_id].append(cell_id)
                ts_for_pop[pop_id].append(t)
                
        
        max_id = 0
        for pop_id in sorted(ids_for_pop.keys()):
            shifted_ids = [id+max_id for id in ids_for_pop[pop_id]]
            
            if pop_id in pop_colors:
                c = pop_colors[pop_id]
            else:
                c = get_next_hex_color()
            
            ax_spikes.plot(ts_for_pop[pop_id], shifted_ids, label=pop_id, linewidth=0, marker='.', color=c)
            
            pop = self.network.get_child(pop_id, 'populations')
            if pop.size is not None:
                max_id_here = evaluate(pop.size, self.network.parameters)
            else:
                max_id_here = max(ids_for_pop[pop_id]) if len(ids_for_pop[pop_id])>0 else 0
                
            print('Finished with spikes for %s, go from %i with max %i'%(pop_id, max_id, max_id_here))
            max_id += max_id_here
            
        ax_spikes.set_xlabel('Time (s)')
        ax_spikes.set_ylabel('Index')
        
        tmax = self.simulation.duration/1000.
        ax_spikes.set_xlim(tmax/-20.0, tmax*1.05)
        ax_spikes.set_ylim(max_id/-20., max_id*1.05)
        
        self.spikesFigure.legend()
        self.spikesCanvas.draw()
                
        print('Done with plotting!')
    

def main():
    """Main run method"""

    app = QApplication(sys.argv)
    
    nml_sim_file = sys.argv[1]

    nmlui = NMLliteUI(nml_sim_file)
    nmlui.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    
