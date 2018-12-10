import collections
import json
from collections import OrderedDict

def print_(text, print_it=False):
    prefix = "neuromllite >>> "
    if not isinstance(text, str): 
        text = ('%s'%text).decode('ascii')
    if print_it:
        
        print("%s%s"%(prefix, text.replace("\n", "\n"+prefix)))
    
    
def print_v(text):
    print_(text, True)

class Base(object):
    
    def __init__(self, **kwargs):
        
        self.__dict__['fields'] = collections.OrderedDict()
        self.__dict__['children'] = collections.OrderedDict()

        for name, value in kwargs.items():       
            #print( ' - Init of %s:  %s = %s'%(self.get_type(),name, value))
            
            if name in self.allowed_fields:
                
                if self._is_base_type(self.allowed_fields[name][1]):
                    self.fields[name] = (self.allowed_fields[name][1])(value)
                else:
                    self.fields[name] = value
            else:
                raise Exception('Error, cannot set %s=%s in %s. Allowed fields here: %s'%(name, value, self.get_type(), self.allowed_fields))
            
    # Will be overridden when id required
    def get_id(self):
        return None
            
            
    def get_type(self):
        return self.__class__.__name__
    
    
    def __getattr__(self, name):
        #print("Checking for attr %s..."%(name))
        '''
        print("Checking %s for attr %s..."%(self.get_id(),name))'''
        
        if name in self.__dict__:
            return self.__dict__[name]
            
        if name=='allowed_fields':
            self.__dict__['allowed_fields'] = collections.OrderedDict()
            return self.__dict__['allowed_fields']
            
        if name=='allowed_children':
            self.__dict__['allowed_children'] = collections.OrderedDict()
            return self.__dict__['allowed_children']
        
        #print self.allowed_fields
        if name in self.allowed_fields:
            if not name in self.fields:
                return None
            return self.fields[name]
        
        if name in self.allowed_children:
            if not name in self.children:
                self.children[name] = []
            return self.children[name]
    
    
    def _is_base_type(self, value):
        return value==int or \
               value==str or \
               value==float
    
    def __setattr__(self, name, value):
        
        #print("   Setting attr %s=%s..."%(name, value))
        
        if name=='allowed_fields' and 'allowed_fields' not in self.__dict__:
            self.__dict__['allowed_fields'] = collections.OrderedDict()
        
        if name=='allowed_children' and 'allowed_children' not in self.__dict__:
            self.__dict__['allowed_children'] = collections.OrderedDict()
        
        if name in self.__dict__:
            self.__dict__[name] = value
            return
        
        if name in self.allowed_fields:
            if self._is_base_type(self.allowed_fields[name][1]):
                   
                self.fields[name] = (self.allowed_fields[name][1])(value)
            else:
                self.fields[name] = value
            return 
        
    def _to_json_element(self, val):
        
        if isinstance(val,str):
            return '"%s"'%val
        
        if isinstance(val,Base):
            return val.to_json(wrap=False)
        
        elif isinstance(val,dict):
            d='{'
            for k in val:
                v = val[k]
                str_v = v.to_json() if isinstance(v,Base) else self._to_json_element(v)
                d+='"%s": %s, '%(k, str_v)
            d=d[:-2]+'}'
            return d
        
        else: 
            return str(val)
        
    
    def to_json(self, pre_indent='', indent='    ', wrap=True):
        
        verbose = False
        #print('Converting to JSON: %s, id: %s (wrapping: %s)'%(self.get_type(),self.get_id(), wrap))
        
        s = pre_indent+('{ ' if wrap else '')
        if self.get_id():
            s += '"%s": {'%(self.get_id())
        else:
            s += '{ '
        if len(self.fields)>0:
            for a in self.allowed_fields:
                if a != 'id':
                    if a in self.fields:
                        ss = self._to_json_element(self.fields[a])
                        s+='\n'+pre_indent+indent +'"%s": '%a+ss+','
                        
        for c in self.allowed_children:
            
            if c in self.children:
                s+='\n'+pre_indent+indent +'"%s": [\n'%(c)
                for cc in self.children[c]:
                    s += cc.to_json(pre_indent+indent+indent,indent, wrap=True)+',\n'
                s=s[:-2]
                s+='\n'+pre_indent+indent +"],"
            
        s=s[:-1]    
        s+=' }'
            
        if wrap:
            s += "\n"+pre_indent+"}" 
            
        if verbose:
            print()
            print("=========== pre <%s> ============="%self)
            print('<%s>'%s)
            
        yy = json.loads(s, object_pairs_hook=OrderedDict)
        ret = json.dumps(yy,indent=4)
        
        if verbose:
            print("============ json ============")
            print(yy)
            print("============ post ============")
            print(ret)
            print("==============================")
        
        return ret
    
    
    def __repr__(self):
        return str(self)
    
    
    def __str__(self):
        s = '%s (%s)'%(self.get_type(),self.get_id())
        for a in self.allowed_fields:
            if a != 'id':
                if a in self.fields:
                    s+=', %s = %s'%(a,self.fields[a])
                    
        for c in self.allowed_children:
            if c in self.children:
                s += '\n  %s:'%(c,)
                for cc in self.children[c]:
                    s += '\n    %s'%(cc)
            
        return s
    
    def __getstate__(self): return self.__dict__
    
    def __setstate__(self, d): self.__dict__.update(d)
    
    def get_child(self, id, type):
        if not type in self.children:
            return None
        for c in self.children[type]:
            if c.id == id:
                return c
            
        return None
        
    

class BaseWithId(Base):
    
    def __init__(self, **kwargs):
        
        self.allowed_fields.update({'id':('Unique ID of element',str), 'notes':('Human readable notes',str)})
        
        super(BaseWithId, self).__init__(**kwargs)
        
            
    def get_id(self):
        if len(self.fields)==0:
            return '???'
        return self.fields['id']
            
            
    def to_json_file(self, file_name=None):
        if not file_name:
            file_name='%s.json'%self.id
        f = open(file_name,'w')
        f.write(self.to_json())
        f.close()
        print_v("Written NeuroMLlite %s to: %s"%(self.__class__.__name__, file_name))
        return file_name
        
        
class NetworkReader():
    
    pop_locations = {}
    
    def parse(self, handler):
        
        raise Exception("This needs to be implemented...")
    
    def get_locations(self):
        
        return self.pop_locations
    
