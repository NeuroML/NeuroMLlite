from neuromllite import *
import sys
    
def print_(text, print_it=False):
    prefix = "neuromllite >>> "
    if not isinstance(text, str): 
        text = ('%s'%text).decode('ascii')
    if print_it:
        
        print("%s%s"%(prefix, text.replace("\n", "\n"+prefix)))
    
    
def print_v(text):
    print_(text, True)
    
def ascii_encode_dict(data):
    ascii_encode = lambda x: x.encode('ascii') if (sys.version_info[0]==2 and isinstance(x, unicode)) else x
    return dict(map(ascii_encode, pair) for pair in data.items()) 
    
def _parse_element(json, to_build):

    for k in json.keys():
        to_build.id = k
        to_build = _parse_attributes(json[k], to_build)
               
    return to_build 
            
def _parse_attributes(json, to_build):
            
    for g in json:
        value = json[g]
        
        #print("  Setting %s=%s (%s) in %s"%(g, value, type(value), to_build))
        if type(to_build)==dict:
            to_build[g]=value
        elif type(value)==str or type(value)==int or type(value)==float:
            to_build.__setattr__(g, value)
        elif type(value)==list:
            type_to_use = to_build.allowed_children[g][1]

            for l in value:
                ff = type_to_use()
                ff = _parse_element(l, ff)
                exec('to_build.%s.append(ff)'%g)
        else:
            type_to_use = to_build.allowed_fields[g][1]
            ff = type_to_use()
            ff = _parse_attributes(value, ff)
            exec('to_build.%s = ff'%g)
                
        
    return to_build
    
    
def load_json(filename):
    import json

    with open(filename, 'r') as f:
        
        data = json.load(f, object_hook=ascii_encode_dict)
        
    return data

    
def load_network_json(filename):
    
    data = load_json(filename)
        
    print_v("Loaded network specification from %s"%filename)
    
    net = Network()
    net = _parse_element(data, net)
    
    return net
    
    
def load_simulation_json(filename):
    import json

    with open(filename, 'r') as f:
        
        data = json.load(f, object_hook=ascii_encode_dict)
        
        
    print_v("Loaded simulation specification from %s"%filename)
    
    sim = Simulation()
    sim = _parse_element(data, sim)
    
    return sim


def evaluate(expr, globals={}):
    
    verbose = False
    print_('Exaluating: [%s] which is a %s vs globals %s...'%(expr,type(expr),globals),verbose)
    try:
        if expr in globals:
            expr = globals[expr]  # replace with the value in globals & check whether it's float/int...
        
        if type(expr)==str:
            try:
                expr = int(expr)
            except:
                pass
            try:
                expr = float(expr)
            except:
                pass
            
        if int(expr)==expr:
            print_('Returning int: %s'%int(expr),verbose)
            return int(expr)
        else: # will have failed if not number
            print_('Returning float: %s'%expr,verbose)
            return float(expr)
    except:
        try:
            print_('Evaluating with python: %s'%expr,verbose)
            return eval(expr, globals)
        except:
            print_('Returning without altering: %s'%expr,verbose)
            return expr