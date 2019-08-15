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
from neuromllite.utils import print_v
from neuromllite.utils import is_spiking_input_population
from pyneuroml.pynml import get_next_hex_color


class NMLliteUI(QWidget):
    
    default_vals = {}
    
    simulators = ['jNeuroML',
        'jNeuroML_NEURON',
        'jNeuroML_NetPyNE',
        'NetPyNE',
        'PyNN_NEURON',
        'PyNN_NEST',
        'PyNN_Brian']
    
    
    def updated_param(self, p):
        """A parameter has been updated"""
        
        print_v('=====   Param %s changed' % p)
        
        if self.autoRunCheckBox.isChecked():
            self.runSimulation()
        else:
            print_v('Nothing changing...')
            
        self.update_net_sim()
        if self.tabs.currentWidget() == self.nmlliteTab:
            self.update_network_json()
            self.update_simulation_json()
        
        
    def update_network_json(self):
        
        self.nmlliteNetText.clear()
        try:
            j = self.network.to_json()
            self.nmlliteNetText.insertPlainText(j)
        except Exception as e:
            self.nmlliteNetText.insertPlainText("Error parsing model: %s"%e)
            
            
    def update_simulation_json(self):
        
        self.nmlliteSimText.clear()
        try:
            j = self.simulation.to_json()
            self.nmlliteSimText.insertPlainText(j)
        except Exception as e:
            self.nmlliteSimText.insertPlainText("Error parsing model: %s"%e)
        
    all_tabs = {}
    #all_tab_layouts = {}
    all_figures = {}
    all_canvases = {}
    
    
    def add_tab(self, name, parent_tab_holder, figure=False, options = False):
        
        thisTab = QWidget()
        parent_tab_holder.addTab(thisTab, name)
        self.all_tabs[name] = thisTab
        
        topLayout = QGridLayout()
        thisTab.setLayout(topLayout)
        
        if options:
            thisOptionsLayout = QGridLayout()
            topLayout.addLayout(thisOptionsLayout, 0, 0)
        
        #self.all_tab_layouts[name] = thisLayout
        
        if figure:
            thisFigure = Figure()
            thisCanvas = FigureCanvas(thisFigure)
            
            self.all_canvases[name] = thisCanvas
            self.all_figures[name] = thisFigure
            if options:
                thisFigureLayout = QGridLayout()
                topLayout.addLayout(thisFigureLayout, 1, 0)
                thisFigureLayout.addWidget(thisCanvas)
            else:
                topLayout.addWidget(thisCanvas)
                
        if options:
            return thisOptionsLayout
        
        
    def get_value_entry(self, name, value, entry_map):
        """Create a graphical element for displaying/setting values"""
        
        simple = False
        simple = True
        
        if simple:
            entry = QLineEdit()
            entry_map[name] = entry
            entry.setText(str(value))
            
            entry.textChanged.connect(self.updated_param)

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
                print_(e)
                
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
        
        
        self.SPIKES_RASTERPLOT = "Rasterplot"
        self.SPIKES_POP_RATE_AVE = "Pop rate averages"
        
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
        self.nmlliteTab = QWidget()
        self.nml2Tab = QWidget()
        self.graphTab = QWidget()
        self.matrixTab = QWidget()
        self.tabs.resize(300, 200)
        
        
        # Add tabs
        self.simTab = QWidget()
        self.tabs.addTab(self.simTab, "Simulation")
        
        self.simTabLayout = QGridLayout()
        self.simTab.setLayout(self.simTabLayout)
        
        self.plotTabs = QTabWidget()
        
        self.tracesTab = QWidget()
        self.plotTabs.addTab(self.tracesTab, "Traces")
        self.heatmapTab = QWidget()
        self.plotTabs.addTab(self.heatmapTab, "Heatmap")
        
        rasterOptionsLayout = self.add_tab(self.SPIKES_RASTERPLOT,self.plotTabs, figure=True, options=True)
        self.rasterLegend = QCheckBox("Show legend")
        self.rasterLegend.setChecked(True)
        rasterOptionsLayout.addWidget(self.rasterLegend, 0, 0)
        self.rasterLegend.toggled.connect(self.replotSimResults)
        self.rasterInPops = QCheckBox("Include input pops")
        self.rasterInPops.setChecked(True)
        rasterOptionsLayout.addWidget(self.rasterInPops, 0, 1)
        self.rasterInPops.toggled.connect(self.replotSimResults)
        
        spikeStatOptionsLayout = self.add_tab(self.SPIKES_POP_RATE_AVE,self.plotTabs, figure=True, options=True)
        self.spikeStatInPops = QCheckBox("Include input pops")
        self.spikeStatInPops.setChecked(True)
        spikeStatOptionsLayout.addWidget(self.spikeStatInPops, 0, 0)
        self.spikeStatInPops.toggled.connect(self.replotSimResults)
        
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
        
        
        self.graphShowExtInputs = QCheckBox("Show ext inputs")
        self.graphShowExtInputs.setChecked(True)
        self.graphTabOptionsLayout.addWidget(self.graphShowExtInputs, 0, 4)
        self.graphShowExtInputs.toggled.connect(self.showGraph)
        
        self.graphShowInputPops = QCheckBox("Show input pops")
        self.graphShowInputPops.setChecked(True)
        self.graphTabOptionsLayout.addWidget(self.graphShowInputPops, 0, 5)
        self.graphShowInputPops.toggled.connect(self.showGraph)
        
        self.graphTabLayout = QGridLayout()
        self.graphTabTopLayout.addLayout(self.graphTabLayout, 1, 0)
        
        
        self.tabs.addTab(self.matrixTab, "Matrix")
        self.matrixTabLayout = QGridLayout()
        self.matrixTab.setLayout(self.matrixTabLayout)
        
        
        # Add tabs
        self.tabs.addTab(self.nmlliteTab, "NeuroMLlite")
        
        self.nmlliteTabLayout = QGridLayout()
        self.nmlliteTab.setLayout(self.nmlliteTabLayout)
        
        self.nmlliteTabs = QTabWidget()
        self.nmlliteTabLayout.addWidget(self.nmlliteTabs)
        
        self.nmlliteSimTab = QWidget()
        self.nmlliteTabs.addTab(self.nmlliteSimTab, "Simulation")
        self.nmlliteSimTabLayout = QGridLayout()
        self.nmlliteSimTab.setLayout(self.nmlliteSimTabLayout)
        self.nmlliteSimText = QPlainTextEdit()
        self.nmlliteSimTabLayout.addWidget(self.nmlliteSimText,0,0)
        
        self.nmlliteNetTab = QWidget()
        self.nmlliteTabs.addTab(self.nmlliteNetTab, "Network")
        self.nmlliteNetTabLayout = QGridLayout()
        self.nmlliteNetTab.setLayout(self.nmlliteNetTabLayout)
        self.nmlliteNetText = QPlainTextEdit()
        self.nmlliteNetTabLayout.addWidget(self.nmlliteNetText,0,0)
        
        
        self.tabs.addTab(self.nml2Tab, "NeuroML 2")
        self.nml2Layout = QGridLayout()
        self.nml2Tab.setLayout(self.nml2Layout)
        self.nml2Text = QPlainTextEdit()
        self.nml2Text.insertPlainText("\n   Generate an instance of the populations and projections in this network in NeuroML 2"+
                                      "\n   format by pressing the Generate NeuroML 2 button on the left"+
                                      "\n\n\n   WARNING: depending on the size of the generated network, text may take some time to load!")
        self.nml2Layout.addWidget(self.nml2Text,0,0)
        
        
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
                
        self.nml2Button = QPushButton("Generate NeuroML 2")
        self.nml2Button.show()
        self.nml2Button.clicked.connect(self.generateNeuroML2)
        
        rows += 1
        paramLayout.addWidget(self.nml2Button, rows, 0)
                
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
        
        self.update_network_json()
        self.update_simulation_json()
 
    
    def showMatrix(self):
        """Generate matrix buttom has been pressed"""
        
        print_v("Matrix button was clicked.")
        
        self.update_net_sim()
        self.tabs.setCurrentWidget(self.matrixTab)
        
        from neuromllite.MatrixHandler import MatrixHandler
        
        level = 2
        
        handler = MatrixHandler(level, nl_network=self.network)
        
        from neuromllite.NetworkGenerator import generate_network
        generate_network(self.network, handler, always_include_props=True, base_dir='.')
    
        print_v("Done with MatrixHandler...")
    
    
    def generateNeuroML2(self):
        """Generate NeuroML 2 representation of network"""
        
        print_v("Generate NeuroML 2 button was clicked.")
        
        self.update_net_sim()
        from neuromllite.NetworkGenerator import generate_neuroml2_from_network
        
        nml_file_name, nml_doc = generate_neuroml2_from_network(self.network, 
                                   print_summary=True, 
                                   seed=self.simulation.seed if self.simulation.seed is not None else 1234, 
                                   format='xml', 
                                   base_dir=None,
                                   copy_included_elements=False,
                                   target_dir=None,
                                   validate=False,
                                   simulation=self.simulation)
                                   
        with open(nml_file_name, 'r') as reader: 
            nml_txt = reader.read()
            
        self.nml2Text.clear()
        self.nml2Text.insertPlainText(nml_txt)
        
        self.tabs.setCurrentWidget(self.nml2Tab)
        
        
        
    
    def showGraph(self):
        """Generate graph buttom has been pressed"""
        
        print_v("Graph button was clicked.")
        
        self.update_net_sim()
        self.tabs.setCurrentWidget(self.graphTab)
        
        from neuromllite.GraphVizHandler import GraphVizHandler
        
        engine = str(self.graphTypeComboBox.currentText()).split(' - ')[1]
        level = int(self.graphLevelComboBox.currentText())
        
        show_ext_inputs = self.graphShowExtInputs.isChecked()
        show_input_pops = self.graphShowInputPops.isChecked()
        
        format = 'svg'
        format = 'png'
        
        handler = GraphVizHandler(level, 
                                  engine=engine, 
                                  nl_network=self.network, 
                                  output_format=format, 
                                  view_on_render=False,
                                  include_ext_inputs=show_ext_inputs,
                                  include_input_pops=show_input_pops)
        
        from neuromllite.NetworkGenerator import generate_network
        generate_network(self.network, handler, always_include_props=True, base_dir='.')
    
        print_v("Done with GraphViz...")
        
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
                
            print_v('Setting param %s to %s' % (p, v))
            self.network.parameters[p] = v
            
        print_v('All params: %s' % self.network.parameters)

        for s in self.sim_entries:
            v = float(self.sim_entries[s].text())
            print_v('Setting simulation variable %s to %s' % (s, v))
            self.simulation.__setattr__(s, v)
        
         
    def runSimulation(self):
        """Run a simulation in the chosen simulator"""
        
        simulator = str(self.simulatorComboBox.currentText())
        print_v("Run button was clicked. Running simulation %s in %s with %s" % (self.simulation.id, self.sim_base_dir, simulator))

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
        
        
    def _get_sorted_population_ids(self, include_input_pops = True):
        all_pop_ids = []
        for pop in self.network.populations:
            if not include_input_pops and is_spiking_input_population(pop, self.network):
                pass # ignoring...
            else:
                all_pop_ids.append(pop.id)
        return sorted(all_pop_ids)
    
    
    def _get_pop_size(self, pop_id):
        pop = self.network.get_child(pop_id, 'populations')
        return evaluate(pop.size, self.network.parameters)
    
    
    def _get_pop_id_cell_id(self, quantity):
        
        if '[' in quantity:
            # e.g. Epop[5]/v
            pop_id = quantity.split('[')[0]
            cell_id = int(quantity.split('[')[1].split(']')[0])
        else:
            # e.g. Epop/0/iafcell/v
            pop_id = quantity.split('/')[0]
            cell_id = int(quantity.split('/')[1])
            
        return pop_id, cell_id


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
        
        spikesFigure = self.all_figures[self.SPIKES_RASTERPLOT]
        ax_spikes = spikesFigure.add_subplot(111)
        ax_spikes.clear()
        
        ids_for_pop = {}
        ts_for_pop = {}
        
        include_input_pops = self.rasterInPops.isChecked()
        pops_to_use = self._get_sorted_population_ids(include_input_pops=include_input_pops)
        
        for k in self.current_events.keys():
            spikes = self.current_events[k]
            
            pop_id, cell_id = self._get_pop_id_cell_id(k)
            if pop_id in pops_to_use:
                if not pop_id in ids_for_pop:
                    ids_for_pop[pop_id] = []
                    ts_for_pop[pop_id] = []

                for t in spikes:
                    ids_for_pop[pop_id].append(cell_id)
                    ts_for_pop[pop_id].append(t)
                
        max_id = 0
                
        for pop_id in sorted(ids_for_pop.keys()):
            
            if pop_id in pop_colors:
                c = pop_colors[pop_id]
            else:
                c = get_next_hex_color()
            
            if pop_id in ts_for_pop:
                shifted_ids = [id+max_id for id in ids_for_pop[pop_id]]
                ax_spikes.plot(ts_for_pop[pop_id], shifted_ids, label=pop_id, linewidth=0, marker='.', color=c)
            
            pop = self.network.get_child(pop_id, 'populations')
            if pop.size is not None:
                max_id_here = self._get_pop_size(pop_id)
            else:
                max_id_here = max(ids_for_pop[pop_id]) if len(ids_for_pop[pop_id])>0 else 0
                
            print_v('Finished with spikes for %s, go from %i with max %i'%(pop_id, max_id, max_id_here))
            max_id += max_id_here
            
        ax_spikes.set_xlabel('Time (s)')
        ax_spikes.set_ylabel('Index')
        
        tmax = self.simulation.duration/1000.
        ax_spikes.set_xlim(tmax/-20.0, tmax*1.05)
        ax_spikes.set_ylim(max_id/-20., max_id*1.05)
        
        if self.rasterLegend.isChecked():
            spikesFigure.legend()
        self.all_canvases[self.SPIKES_RASTERPLOT].draw()
        
        
        ## Plot pop spike rates
        
        popRateFigure = self.all_figures[self.SPIKES_POP_RATE_AVE]
        ax_pop_rate = popRateFigure.add_subplot(111)
        ax_pop_rate.clear()
        
        rates = {}
        print_v('Generating rates from %s'%self.current_events.keys())
        
        xs = []
        labels = []
        pop_sizes = {}
        count = 0
        rates = {}
        
        include_input_pops = self.spikeStatInPops.isChecked()
        pops_to_use = self._get_sorted_population_ids(include_input_pops=include_input_pops)
        
        for pop_id in pops_to_use:
            xs.append(count)
            labels.append(pop_id)
            count +=1 
            pop_sizes[pop_id] = self._get_pop_size(pop_id)
            rates[pop_id] = []
                
        for k in self.current_events.keys():
            spikes = self.current_events[k]
            pop_id, cell_id = self._get_pop_id_cell_id(k)
            if pop_id in pops_to_use:
                rate = 1000*len(spikes)/self.simulation.duration
                print_v('%s: %s[%s] has %s spikes, so %s Hz'%(k, pop_id, cell_id, len(spikes), rate))
                rates[pop_id].append(rate)
        
        avg_rates = []
        sd_rates = []
        import numpy as np
        
        for pop_id in pops_to_use:
            avg_rates.append(np.mean(rates[pop_id]) if len(rates[pop_id])>0 else 0)
            sd_rates.append(np.std(rates[pop_id]) if len(rates[pop_id])>0 else 0)
        
        print('Rates: %s; means: %s; stds: %s'%(rates,avg_rates,sd_rates))
        
        bars = ax_pop_rate.bar(xs, avg_rates, yerr=sd_rates)
        
        ax_pop_rate.set_ylabel('Rate (Hz)')
        for bi in range(len(bars)):
            bar = bars[bi]
            bar.set_facecolor(pop_colors[labels[bi]])
        
        ax_pop_rate.set_xticks(xs)
        ax_pop_rate.set_xticklabels(labels)
        ax_pop_rate.set_xticklabels(ax_pop_rate.get_xticklabels(), rotation=45, horizontalalignment='right')
        
        self.all_canvases[self.SPIKES_POP_RATE_AVE].draw()
                
        print_v('Done with plotting!')
    

def main():
    """Main run method"""

    app = QApplication(sys.argv)
    
    nml_sim_file = sys.argv[1]

    nmlui = NMLliteUI(nml_sim_file)
    nmlui.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    
