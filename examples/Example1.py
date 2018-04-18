from neuromllite import Network, Population, Projection, RandomConnectivity


################################################################################
###   Build a new network

net = Network(id='net0')
net.notes = "A simple network with 2 populations & projection between them. "+ \
            "No info yet on what the cells are so network can't be simulated."

print(net)


################################################################################
###   Add some populations

p0 = Population(id='pop0', size=5, component='iaf')
p1 = Population(id='pop1', size=10, component='iaf')

print(p1.to_json())

net.populations.append(p0)
net.populations.append(p1)


################################################################################
###   Add a projection

net.projections.append(Projection(id='proj0',
                                  presynaptic=p0.id, 
                                  postsynaptic=p1.id,
                                  synapse='ampa'))
                                  
net.projections[0].random_connectivity=RandomConnectivity(probability=0.5)


################################################################################
###   Save to JSON format
                                 
print(net)
net.id = 'TestNetwork'

print(net.to_json())
net.to_json_file('Example1_%s.json'%net.id)
