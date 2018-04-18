from neuromllite import *
    
def print_(text, print_it=False):
    prefix = "neuromllite >>> "
    if not isinstance(text, str): 
        text = ('%s'%text).decode('ascii')
    if print_it:
        
        print("%s%s"%(prefix, text.replace("\n", "\n"+prefix)))
    
    
def print_v(text):
    print_(text, True)
    
def ascii_encode_dict(data):
    ascii_encode = lambda x: x.encode('ascii') if isinstance(x, unicode) else x
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
    
    
def load_network_json(filename):
    import json

    with open(filename, 'r') as f:
        
        data = json.load(f, object_hook=ascii_encode_dict)
        
        
    print_v("Loaded network specification from %s"%filename)
    
    net = Network()
    net = _parse_element(data, net)
    
    return net


def evaluate(expr, globals={}):
    #print_v('Exaluating: [%s]...'%expr)
    try:
        if int(expr)==expr:
            return int(expr)
        else: # will have failed if not number
            return float(expr)
    except:
        return eval(expr, globals)