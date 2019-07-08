
from os.path import dirname, realpath
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

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

        '''
        addressLabel = QLabel("Address:")
        self.addressText = QTextEdit()
        self.addressText.setText(sim.to_json())
        self.addressText.setReadOnly(True)'''

        mainLayout = QGridLayout()
        rows = 0
        mainLayout.addWidget(nameLabel, rows, 0)
        mainLayout.addWidget(self.nameLine, rows, 1)
        #mainLayout.addWidget(addressLabel, 1, 0, Qt.AlignTop)
        ##mainLayout.addWidget(self.addressText, 1, 1)
        
        
        rows+=1
        mainLayout.addWidget(QLabel("Simulation parameters"), rows, 0)

        self.sim_entries = {}
        svars = ['dt','duration','seed']

        for s in svars:
            rows+=1
            sval = self.simulation.__getattr__(s)
            if sval is not None:
                label = QLabel("%s"%s)
                mainLayout.addWidget(label, rows, 0)
                
                txt = QLineEdit()
                self.sim_entries[s] = txt
                txt.setText(str(sval))
                mainLayout.addWidget(txt, rows, 1)

        rows+=1
        mainLayout.addWidget(QLabel("Network parameters"), rows, 0)
        
        self.param_entries = {}

        for p in sorted(self.network.parameters.keys()):
            rows+=1
            param = self.network.parameters[p]
            label = QLabel("%s"%p)
            mainLayout.addWidget(label, rows, 0)
            txt = QLineEdit()
            self.param_entries[p] = txt
            txt.setText(str(param))
            mainLayout.addWidget(txt, rows, 1)

        self.runButton = QPushButton("Run simulation")
        self.runButton.show()
        
        self.runButton.clicked.connect(self.runSimulation)
        
        
        rows+=1
        buttonLayout1 = QVBoxLayout()
        buttonLayout1.addWidget(self.runButton, Qt.AlignTop)
        buttonLayout1.addStretch()

        mainLayout.addLayout(buttonLayout1, rows, 0)

        self.setLayout(mainLayout)
        self.setWindowTitle("NeuroMLlite GUI")
 



        self.simulator='jNeuroML'
    
    def runSimulation(self):
        print("Button was clicked. Running simulation %s in %s"%(self.simulation.id, self.sim_base_dir))

        for p in self.param_entries:
            v = float(self.param_entries[p].text())
            print('Setting param %s to %s'%(p,v))
            self.network.parameters[p] = v

        for s in self.sim_entries:
            v = float(self.sim_entries[s].text())
            print('Setting simulation variable %s to %s'%(s,v))
            self.simulation.__setattr__(s,v)

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

        from pyneuroml.pynml import generate_plot

        xs = []
        ys = []
        labels = []

        for key in traces:

            if key != 't':
                xs.append(traces['t'])
                ys.append(traces[key])
                labels.append(key)

        generate_plot(xs,ys,'Results',labels=labels, xaxis="Time (s)",legend_position='right')



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
