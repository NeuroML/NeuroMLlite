from os.path import dirname
from os.path import realpath
import sys

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from matplotlib.backends.backend_qt5agg import FigureCanvas 
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import matplotlib
from matplotlib.figure import Figure

from neuromllite.utils import load_network_json
from neuromllite.utils import load_simulation_json
from neuromllite.utils import evaluate
from neuromllite.utils import print_v, print_
from neuromllite.utils import is_spiking_input_population
from pyneuroml.pynml import get_next_hex_color

from functools import partial

class ParameterSpinBox(QDoubleSpinBox):
    
    #TODO: handle a spinner on values like -60mV etc. 
    def textFromValue(self, value):
        return '%s'%value
    

class NMLliteUI(QWidget):
    
    default_vals = {}
    
    simulators = ['jNeuroML',
        'jNeuroML_NEURON',
        'jNeuroML_NetPyNE',
        'NetPyNE',
        'PyNN_NEURON',
        'PyNN_NEST',
        'PyNN_Brian',
        'Arbor']
    '''    'jNeuroML_Brian2','''
        
    LEMS_VIEW_TAB = 'Lems View'
    IMAGE_3D_TAB = "3D image"
    GRAPH_TAB = 'Graph'
    
    verbose=False
    
    def updated_param(self, p):
        """A parameter has been updated"""
        
        print_('=====   Param %s changed' % p, self.verbose)
        
        if self.autoRunCheckBox.isChecked():
            self.runSimulation()
        else:
            print_('Nothing changing...', self.verbose)
            
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
    all_figures_2dplots = {}
    all_canvases = {}
    all_layouts = {}
    all_options_layouts = {}
    all_image_qlabels = {}
    all_image_scales = {}
    
    current_traces_shown = {}
    current_traces_colours = {}
     
    def add_tab(self, name, parent_tab_holder, image=False, figure=False, toolbar=False, options = False):
        
        if name in self.all_tabs:
            raise Exception('The name for a tab: %s is already taken!'%name)
        
        thisTab = QWidget()
        parent_tab_holder.addTab(thisTab, name)
        self.all_tabs[name] = thisTab
        
        topLayout = QGridLayout()
        thisTab.setLayout(topLayout)
        self.all_layouts[name] = topLayout
        
        if options:
            thisOptionsLayout = QGridLayout()
            topLayout.addLayout(thisOptionsLayout, 0, 0)
            thisOptionsLayout.addWidget(QLabel("Options:"), 0, 0)
            self.all_options_layouts[name] = thisOptionsLayout
        
        if figure:
            thisFigure = Figure()
            thisCanvas = FigureCanvas(thisFigure)
            if toolbar: thisToolbar = NavigationToolbar(thisCanvas, self)
             
            self.all_canvases[name] = thisCanvas
            self.all_figures[name] = thisFigure
            if options:
                thisFigureLayout = QGridLayout()
                topLayout.addLayout(thisFigureLayout, 1, 0)
                thisFigureLayout.addWidget(thisCanvas)
                if toolbar: thisFigureLayout.addWidget(thisToolbar)
            else:
                topLayout.addWidget(thisCanvas)
                if toolbar: topLayout.addWidget(thisToolbar)
                
        if image:
            label = QLabel("An image will be generated here. Push the appropriate button on the left")
            label.setBackgroundRole(QPalette.Base)
            label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            label.setScaledContents(True)
            self.all_image_qlabels[name] = label
        
            scrollArea = QScrollArea()
            scrollArea.setBackgroundRole(QPalette.Light)
            scrollArea.setWidget(label)
            scrollArea.setVisible(True)

            scroolLayout = QGridLayout()
            topLayout.addLayout(scroolLayout, 1, 0)
            scroolLayout.addWidget(scrollArea, 0, 0)
            
            if options:
                plus_button = QPushButton("+")
                plus_button.show()
                plus_button.clicked.connect(partial(self.scale_image,name,'+'))
                thisOptionsLayout.addWidget(plus_button, 0, 1)
                orig_button = QPushButton("1")
                orig_button.show()
                orig_button.clicked.connect(partial(self.scale_image,name,'1'))
                thisOptionsLayout.addWidget(orig_button, 0, 2)
                min_button = QPushButton("-")
                min_button.show()
                min_button.clicked.connect(partial(self.scale_image,name,'-'))
                thisOptionsLayout.addWidget(min_button, 0, 3)
                
        if options:
            return thisOptionsLayout
          
    def scale_image(self, tab_reference, action):
        scaleFactor = self.all_image_scales[tab_reference]
        
        print('Scaling with: %s on %s, was %s'%(action, tab_reference, scaleFactor))
        if action == '+':
            self.all_image_scales[tab_reference] *=1.25
        if action == '-':
            self.all_image_scales[tab_reference] *=0.8
        if action == '1':
            self.all_image_scales[tab_reference] = 1
            
        label = self.all_image_qlabels[tab_reference]
        label.resize(self.all_image_scales[tab_reference] * label.pixmap().size())
        
        
    def add_image(self, image_file, tab_reference):
        # Inspired by https://gist.github.com/acbetter/32c575803ec361c3e82064e60db4e3e0
        
        print_v('Displaying an image: %s'%(image_file))
        
        image = QImage(image_file)
        pixmap = QPixmap.fromImage(image)
        
        label = self.all_image_qlabels[tab_reference]
        #pixmap = pixmap.scaledToWidth(min(pixmap.width(), 800), Qt.SmoothTransformation)
        label.setPixmap(pixmap)
        self.all_image_scales[tab_reference] = 1
        scaleFactor = self.all_image_scales[tab_reference]
        
        label.resize(scaleFactor * label.pixmap().size())
        
        
    def get_value_entry(self, name, value, entry_map):
        """Create a graphical element for displaying/setting values"""
        
        simple = False
        #simple = True
        
        if simple:
            entry = QLineEdit()
            entry_map[name] = entry
            entry.setText(str(value))
            entry.textChanged.connect(self.updated_param)

        else:
        
            try:
                entry = ParameterSpinBox()
                entry_map[name] = entry
                entry.setDecimals(18)
                entry.setMaximum(1e16)
                entry.setMinimum(-1e16)
                entry.setSingleStep(value / 20.0)
                entry.setValue(float(value))
                entry.valueChanged.connect(self.updated_param)
                
            except Exception as e:
                print_v('Error: %s'%e)
                
                entry = QLineEdit()
                entry_map[name] = entry
                entry.setText(str(value))
                entry.textChanged.connect(self.updated_param)
        
        entry.setToolTip('Parameter: %s (initial value: %s)'%(name,value))  
        
        print_('Created value entry widget for %s (= %s): %s (%s)' % \
              (name, value, entry, entry.text()), self.verbose)
        return entry
    
    
    def dialog_popup(self, message):
        dialog=QMessageBox()
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle('Message')
        dialog.setText(message)
        dialog.exec_()
    
    
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
        
        if self.simulation.plots2D is not None:
            
            self.plot2DTab = QTabWidget()
            self.plotTabs.addTab(self.plot2DTab, "2D plots")

            self.plot2DTabLayout = QGridLayout()
            self.plot2DTab.setLayout(self.plot2DTabLayout)
        
            for plot2D in self.simulation.plots2D:
                info = self.simulation.plots2D[plot2D]
                pLayout = self.add_tab(plot2D, self.plot2DTab, figure=True, toolbar=True, options=True)
        
        if self.simulation.plots3D is not None:
            
            self.plot3DTab = QTabWidget()
            self.plotTabs.addTab(self.plot3DTab, "3D plots")

            self.plot3DTabLayout = QGridLayout()
            self.plot3DTab.setLayout(self.plot3DTabLayout)
        
            for plot3D in self.simulation.plots3D:
                info = self.simulation.plots3D[plot3D]
                pLayout = self.add_tab(plot3D, self.plot3DTab, figure=True, toolbar=False, options=True)
                
        
        offset_opt = 1
        rasterOptionsLayout = self.add_tab(self.SPIKES_RASTERPLOT,self.plotTabs, figure=True, toolbar=True, options=True)
        self.rasterLegend = QCheckBox("Show legend")
        self.rasterLegend.setChecked(True)
        rasterOptionsLayout.addWidget(self.rasterLegend, 0, 0+offset_opt)
        self.rasterLegend.toggled.connect(self.replotSimResults)
        self.rasterInPops = QCheckBox("Include input pops")
        self.rasterInPops.setChecked(True)
        rasterOptionsLayout.addWidget(self.rasterInPops, 0, 1+offset_opt)
        self.rasterInPops.toggled.connect(self.replotSimResults)
        
        spikeStatOptionsLayout = self.add_tab(self.SPIKES_POP_RATE_AVE,self.plotTabs, figure=True, toolbar=True, options=True)
        self.spikeStatInPops = QCheckBox("Include input pops")
        self.spikeStatInPops.setChecked(True)
        spikeStatOptionsLayout.addWidget(self.spikeStatInPops, 0, 0+offset_opt)
        self.spikeStatInPops.toggled.connect(self.replotSimResults)
        
        self.simTabLayout.addWidget(self.plotTabs)
        
        self.tracesTabTopLayout = QGridLayout()
        self.tracesTab.setLayout(self.tracesTabTopLayout)
        
        self.tracesTabOptionsLayout = QGridLayout()
        self.tracesTabTopLayout.addLayout(self.tracesTabOptionsLayout, 0, 0)
        
        self.showTracesLegend = QCheckBox("Legend")
        self.tracesTabOptionsLayout.addWidget(self.showTracesLegend, 0, 0)
        
        self.traceSelectButton = QPushButton("Select traces...")
        self.traceSelectButton.show()
        self.traceSelectButton.setEnabled(False)
        
        self.traceSelectButton.clicked.connect(self.traceSelect)
        self.tracesTabOptionsLayout.addWidget(self.traceSelectButton, 0, 1)
        
        self.tracesTabLayout = QGridLayout()
        self.tracesTabTopLayout.addLayout(self.tracesTabLayout, 1, 0)
        
        self.heatmapLayout = QGridLayout()
        self.heatmapTab.setLayout(self.heatmapLayout)
        self.heatmapColorbar = None
        
        self.tracesFigure = Figure()
        self.tracesCanvas = FigureCanvas(self.tracesFigure)
        self.tracesToolbar = NavigationToolbar(self.tracesCanvas, self)
        self.tracesTabLayout.addWidget(self.tracesCanvas)
        self.tracesTabLayout.addWidget(self.tracesToolbar)
        
        self.heatmapFigure = Figure()
        self.heatmapCanvas = FigureCanvas(self.heatmapFigure)
        self.heatmapLayout.addWidget(self.heatmapCanvas)
        
        
        self.add_tab(self.GRAPH_TAB, self.tabs, image=True, options = True)
        
        graphTabOptionsLayout = self.all_options_layouts[self.GRAPH_TAB]
        
        offset_opt = 4
        graphTabOptionsLayout.addWidget(QLabel("Graph level:"), 0, offset_opt+0)
        
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
        graphTabOptionsLayout.addWidget(self.graphLevelComboBox, 0, offset_opt+1)
        self.graphLevelComboBox.currentIndexChanged.connect(self.showGraph)
        
        self.graphTypeComboBox = QComboBox(self)
        self.graphTypeComboBox.addItem('d - dot')
        self.graphTypeComboBox.addItem('c - circo')
        self.graphTypeComboBox.addItem('n - neato')
        self.graphTypeComboBox.addItem('f - fdp')
        self.graphTypeComboBox.setCurrentIndex(0)
        graphTabOptionsLayout.addWidget(QLabel("GraphViz engine:"), 0, offset_opt+2)
        graphTabOptionsLayout.addWidget(self.graphTypeComboBox, 0, offset_opt+3)
        self.graphTypeComboBox.currentIndexChanged.connect(self.showGraph)
        
        
        self.graphShowExtInputs = QCheckBox("Show ext inputs")
        self.graphShowExtInputs.setChecked(True)
        graphTabOptionsLayout.addWidget(self.graphShowExtInputs, 0, offset_opt+4)
        self.graphShowExtInputs.toggled.connect(self.showGraph)
        
        self.graphShowInputPops = QCheckBox("Show input pops")
        self.graphShowInputPops.setChecked(True)
        graphTabOptionsLayout.addWidget(self.graphShowInputPops, 0, offset_opt+5)
        self.graphShowInputPops.toggled.connect(self.showGraph)
        
        
        self.add_tab(self.LEMS_VIEW_TAB, self.tabs, image=True, options = True)
        
        self.add_tab(self.IMAGE_3D_TAB, self.tabs, image=True, options = True)        
        
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
        
        if self.network.seed is not None:
            rows += 1
            pval = self.network.seed
            label = QLabel('Net generation seed')
            paramLayout.addWidget(label, rows, 0)
            entry = self.get_value_entry('seed', pval, self.param_entries)
            paramLayout.addWidget(entry, rows, 1)
            
        if self.network.temperature is not None:
            rows += 1
            pval = self.network.temperature
            label = QLabel('Temperature')
            paramLayout.addWidget(label, rows, 0)
            entry = self.get_value_entry('temperature', pval, self.param_entries)
            paramLayout.addWidget(entry, rows, 1)
            
                
                
        self.graphButton = QPushButton("Generate graph")
        self.graphButton.show()
        self.graphButton.clicked.connect(self.showGraph)
        
        rows += 1
        paramLayout.addWidget(self.graphButton, rows, 0)
                
        self.lemsViewButton = QPushButton("Generate LEMS View")
        self.lemsViewButton.show()
        self.lemsViewButton.clicked.connect(self.showLemsView)
        
        rows += 1
        paramLayout.addWidget(self.lemsViewButton, rows, 0)
                
        self.image3DButton = QPushButton("Generate 3D image")
        self.image3DButton.show()
        self.image3DButton.clicked.connect(self.show3Dimage)
        
        rows += 1
        paramLayout.addWidget(self.image3DButton, rows, 0)
                
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
        
        if len(self.network.projections) == 0:
            self.dialog_popup('No projections present in network, and so no matrix to show')
            return
        
        self.update_net_sim()
        self.tabs.setCurrentWidget(self.matrixTab)
        
        from neuromllite.MatrixHandler import MatrixHandler
        
        level = 2
        
        handler = MatrixHandler(level, nl_network=self.network)
        
        from neuromllite.NetworkGenerator import generate_network
        generate_network(self.network, handler, always_include_props=True, base_dir='.')
    
        print_("Done with MatrixHandler...", self.verbose)
    
    
    def generateNeuroML2(self):
        """Generate NeuroML 2 representation of network"""
        
        print_v("Generate NeuroML 2 button was clicked.")
        
        self.update_net_sim()
        from neuromllite.NetworkGenerator import generate_neuroml2_from_network
        
        nml_file_name, nml_doc = generate_neuroml2_from_network(self.network, 
                                   print_summary=True, 
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
        
        
        
    
    def showLemsView(self):
        """Generate lemsView button has been pressed"""
        
        print_v("lemsView button was clicked.")
        
        self.update_net_sim()
        self.tabs.setCurrentWidget(self.all_tabs[self.LEMS_VIEW_TAB])
        self.update_net_sim()
        from neuromllite.NetworkGenerator import generate_neuroml2_from_network
        
        from neuromllite.NetworkGenerator import generate_and_run
       
        lems_file_name = generate_and_run(self.simulation,
                                          simulator='jNeuroML_norun',
                                          network=self.network,
                                          return_results=False,
                                          base_dir=self.sim_base_dir)
                                          
        post_args = "-graph"

        from pyneuroml.pynml import run_jneuroml
        run_jneuroml("", 
                     lems_file_name, 
                     post_args, 
                     verbose = True)
                     
        lems_view_file = lems_file_name.replace('.xml','.png')
                    
        self.add_image(lems_view_file, self.LEMS_VIEW_TAB)   
        
        
    def show3Dimage(self):
        """Generate 3D view button has been pressed"""
        
        print_v("image3D button was clicked.")
        
        self.update_net_sim()
        self.tabs.setCurrentWidget(self.all_tabs[self.IMAGE_3D_TAB])

        from neuromllite.NetworkGenerator import generate_neuroml2_from_network
        
        nml_file_name, nml_doc = generate_neuroml2_from_network(self.network, 
                                   print_summary=True, 
                                   format='xml', 
                                   base_dir=None,
                                   copy_included_elements=False,
                                   target_dir=None,
                                   validate=False,
                                   simulation=self.simulation)
                                          
        post_args = "-png"

        from pyneuroml.pynml import run_jneuroml
        run_jneuroml("", 
                     nml_file_name, 
                     post_args, 
                     verbose = True)
                     
        nml_view_file = nml_file_name.replace('.nml','.png')
                    
        self.add_image(nml_view_file, self.IMAGE_3D_TAB)               
                                   
        
    
    def showGraph(self):
        """Generate graph buttom has been pressed"""
        
        print_v("Graph button was clicked.")
        
        self.update_net_sim()
        self.tabs.setCurrentWidget(self.all_tabs[self.GRAPH_TAB])
        
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
    
        print_("Done with GraphViz...", self.verbose)
        
        if format == 'svg':
            genFile = '%s.gv.svg' % self.network.id
            
            self.add_image(genFile, self.GRAPH_TAB)
            '''
            svgWidget = QSvgWidget(genFile)
            svgWidget.resize(svgWidget.sizeHint())
            svgWidget.show()
            self.graphTabLayout.addWidget(svgWidget, 0, 0)'''
            
        elif format == 'png':
            genFile = '%s.gv.png' % self.network.id

            self.add_image(genFile, self.GRAPH_TAB)
    
        
        
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
                
            print_('Setting param %s to %s' % (p, v), self.verbose)
            if p=='seed':
                self.network.seed = v
            elif p=='temperature':
                self.network.temperature = v
            else:
                self.network.parameters[p] = v
            
        print_('All params: %s' % self.network.parameters, self.verbose)

        for s in self.sim_entries:
            v = float(self.sim_entries[s].text())
            print_('Setting simulation variable %s to %s' % (s, v), self.verbose)
            self.simulation.__setattr__(s, v)
        
         
    def runSimulation(self):
        """Run a simulation in the chosen simulator"""
        
        simulator = str(self.simulatorComboBox.currentText())
        print("Run button was clicked. Running simulation %s in %s with %s" % (self.simulation.id, self.sim_base_dir, simulator))

        self.tabs.setCurrentWidget(self.simTab)
        
        self.update_net_sim()
        

        from neuromllite.NetworkGenerator import generate_and_run
        #return
        try:
            self.current_traces, self.current_events = generate_and_run(self.simulation,
                                              simulator=simulator,
                                              network=self.network,
                                              return_results=True,
                                              base_dir=self.sim_base_dir)

            self.replotSimResults()
        except Exception as e:
            self.dialog_popup('Error: %s'%e)
        
        
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

        
    def traceSelect(self):
        
        print_v("traceSelect button was clicked. Traces shown: %s; colours: %s"%(self.current_traces_shown,self.current_traces_colours))

        dialog = QDialog(self)
        dialog.setWindowTitle("Select which traces to plot")
        
        QBtn = QDialogButtonBox.Ok # | QDialogButtonBox.Cancel
        
        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(dialog.accept)

        layout = QGridLayout()
        dialog.setLayout(layout)
        
        count = 0
        self.all_cbs = {}
        
        for key in sorted(self.current_traces.keys()):
            if key != 't':
                self.all_cbs[key] = QCheckBox(key)
                self.all_cbs[key].setChecked(self.current_traces_shown[key])
                self.all_cbs[key].stateChanged.connect(partial(self.traceSelectClicked,key))
                color_button = QPushButton("%s"%self.current_traces_colours[key])
                style = 'QPushButton {background-color: %s; color: black;}'%self.current_traces_colours[key]
                color_button.setStyleSheet(style)
                
                layout.addWidget(color_button,count,0)
                layout.addWidget(self.all_cbs[key],count,1)
                count+=1
            
        layout.addWidget(buttonBox,count,1)
        dialog.exec_()
        self.replotSimResults()
            
            
    def traceSelectClicked(self, key):

        cb = self.all_cbs[key]
        #print('Clicked: %s, %s, key: %s'%(cb.text(),cb.isChecked(), key))
        self.current_traces_shown[key] = cb.isChecked()
        
        
    def _eval_at_all(self, expr, parameters, traces):
        tr_present = []
        for t in traces:
            if t !='t' and t in expr:
                tr_present.append(t)
                
        ret_val = []
        
        num_vals = len(traces[tr_present[0]])
        print_('Evaluating %s with traces: %s (%i values) and params: %s'%(expr, tr_present, num_vals, parameters.keys()), self.verbose)
            
        for i in range(num_vals):
            noo = expr
            for t in tr_present:
                noo = noo.replace(t,str(traces[tr_present[0]][i]))
                #print_v('%i: %s -> %s'%(i, expr, noo))
            
            r = evaluate(noo, parameters)
            ret_val.append(float(r))
        print_('Generated: %s->%s (#%s)'%(ret_val[0],ret_val[-1], len(ret_val)), self.verbose)
        return ret_val
     

    def replotSimResults(self):
        
        simulator = str(self.simulatorComboBox.currentText())
        self.traceSelectButton.setEnabled(True)

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

            if not key in self.current_traces_shown:
                self.current_traces_shown[key] = True
                
            if key != 't':
                heat_array.append(self.current_traces[key])
                pop_id = key.split('/')[0]
                
                if self.current_traces_shown[key]:
                    chosen_color = None

                    if key in self.current_traces_colours:
                        #print 'using stored for %s'%key
                        chosen_color = self.current_traces_colours[key]
                        colors.append(chosen_color)
                    else:
                        #print 'using new for %s'%key
                        if pop_id in pop_colors and not pop_colors[pop_id] in colors_used:
                            chosen_color = pop_colors[pop_id]
                            colors_used.append(pop_colors[pop_id])
                        else:
                            if key in self.backup_colors:
                                chosen_color = self.backup_colors[key]
                            else:
                                chosen_color = get_next_hex_color()
                                self.backup_colors[key] = chosen_color

                        colors.append(chosen_color)
                        self.current_traces_colours[key] = chosen_color
                    
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
        
        if len(heat_array)>0:
            cm = matplotlib.cm.get_cmap('jet')
            hm = ax_heatmap.pcolormesh(heat_array, cmap=cm)
            #cbar = ax_heatmap.colorbar(im)

            if self.heatmapColorbar == None:
                self.heatmapColorbar = self.heatmapFigure.colorbar(hm)
                self.heatmapColorbar.set_label('Firing rate')

            self.heatmapCanvas.draw()
        
        
        ## Plot 2D 
        
        if self.simulation.plots2D is not None:
            
            for plot2D in self.simulation.plots2D:
                info = self.simulation.plots2D[plot2D]
                fig = self.all_figures[plot2D]
                
                ax_2d = fig.add_subplot(111)
                ax_2d.clear()
                    
                x_axes = info['x_axis']
                y_axes = info['y_axis']
                
                if not type(x_axes) == dict:
                    x_axes = {plot2D:x_axes}
                    y_axes = {plot2D:y_axes}
                    
                for a in x_axes:
                    x_axis = x_axes[a]
                    y_axis = y_axes[a]

                    ax_2d.set_xlabel(x_axis)
                    ax_2d.set_ylabel(y_axis)

                    print_('Plotting %s for %s in %s: %s'%(a,plot2D, fig, info), self.verbose)

                    if x_axis in self.current_traces.keys():
                        xs = self.current_traces[x_axis]
                    else:
                        xs = self._eval_at_all(x_axis, self.network.parameters, self.current_traces)
                    if y_axis in self.current_traces.keys():
                        ys = self.current_traces[y_axis]
                    else:
                        ys = self._eval_at_all(y_axis, self.network.parameters, self.current_traces)
                        
                    ax_2d.plot(xs,ys, linewidth=0.5, label=a)

                    from pyneuroml.analysis.NML2ChannelAnalysis import get_colour_hex
                    
                    num_points = len(xs)
                    tot_dots = 2
                    if a!='a':
                        tot_dots=2
                    for i in range(tot_dots):
                        fract = i/float(tot_dots-1)

                        index = int(num_points*fract)
                        if index>=num_points:
                            index = -1
                        c = '%s'%get_colour_hex(fract, (0, 255, 0), (255, 0, 0))
                        #print('Point %s/%s, fract %s, index %i, %s'%(i,tot_dots, fract,index, c))
                        m = 4 if index==0 or index==-1 else 2
                        ax_2d.plot(xs[index],ys[index], 'o', color=c, markersize=m)
                fig.legend()
                
                self.all_canvases[plot2D].draw()
        
        ## Plot 3D 
        
        if self.simulation.plots3D is not None:
            
            for plot3D in self.simulation.plots3D:
                info = self.simulation.plots3D[plot3D]
                fig = self.all_figures[plot3D]
                
                #ax_3d = fig.add_subplot(111)
                from mpl_toolkits.mplot3d import Axes3D
                ax_3d = fig.gca(projection='3d')
                
                ax_3d.clear()
                xs = self.current_traces[info['x_axis']]
                ys = self.current_traces[info['y_axis']]
                zs = self.current_traces[info['z_axis']]
                
                
                num_points = len(xs)
                tot_dots = 300
                for i in range(tot_dots):
                    fract = i/float(tot_dots-1)
                    
                    index = int(num_points*fract)
                    if index>=num_points:
                        index = -1
                    c = '%s'%get_colour_hex(fract, (0, 255, 0), (255, 0, 0))
                    #print('Point %s/%s, fract %s, index %i, %s'%(i,tot_dots, fract,index, c))
                    m = 4 if index==0 or index==-1 else 1.5
                    ax_3d.plot([xs[index]],[ys[index]],[zs[index]], 'o', color=c, markersize=m)
                    
                ax_3d.plot(xs,ys,zs, linewidth=0.5)
                ax_3d.set_xlabel(info['x_axis'])
                ax_3d.set_ylabel(info['y_axis'])
                ax_3d.set_zlabel(info['z_axis'])
                
                print('Plotting for %s in %s: %s'%(plot3D, fig, info))
                
                self.all_canvases[plot3D].draw()
                
        
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
                
            print_('Finished with spikes for %s, go from %i with max %i'%(pop_id, max_id, max_id_here), self.verbose)
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
        print_('Generating rates from %s'%self.current_events.keys(), self.verbose)
        
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
                print_('%s: %s[%s] has %s spikes, so %s Hz'%(k, pop_id, cell_id, len(spikes), rate), self.verbose)
                rates[pop_id].append(rate)
        
        avg_rates = []
        sd_rates = []
        import numpy as np
        
        for pop_id in pops_to_use:
            avg_rates.append(np.mean(rates[pop_id]) if len(rates[pop_id])>0 else 0)
            sd_rates.append(np.std(rates[pop_id]) if len(rates[pop_id])>0 else 0)
        
        print_v('Calculated rates: %s; means: %s; stds: %s'%(rates,avg_rates,sd_rates))
        
        bars = ax_pop_rate.bar(xs, avg_rates, yerr=sd_rates)
        
        ax_pop_rate.set_ylabel('Rate (Hz)')
        for bi in range(len(bars)):
            bar = bars[bi]
            bar.set_facecolor(pop_colors[labels[bi]])
        
        ax_pop_rate.set_xticks(xs)
        ax_pop_rate.set_xticklabels(labels)
        ax_pop_rate.set_xticklabels(ax_pop_rate.get_xticklabels(), rotation=45, horizontalalignment='right')
        
        self.all_canvases[self.SPIKES_POP_RATE_AVE].draw()
                
        print_v('Finished plotting')
    

def main():
    """Main run method"""
    
    if len(sys.argv)==1:
        usage()
        exit()

    app = QApplication(sys.argv)
    nml_sim_file = sys.argv[1]

    nmlui = NMLliteUI(nml_sim_file)
    nmlui.show()

    sys.exit(app.exec_())

def usage():
    
    from neuromllite import __version__ as version
    MAIN_CLA = 'nmllite-ui'
    USAGE = '''
NMLlite-UI v{0}: A GUI for loading NeuroMLlite files    

Usage:
    {1} Sim_xxx.json  
         Load a NeuroMLlite file containing a Simulation, which refers to the Network to run
    '''.format(version, MAIN_CLA)
    print(USAGE)

if __name__ == '__main__':
    main()
    
