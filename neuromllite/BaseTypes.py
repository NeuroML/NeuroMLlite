import collections
import json
from collections import OrderedDict

verbose = False

def print_(text, print_it=False):
    """
    Print a message preceded by neuromllite, only if print_it=True
    """
    prefix = "neuromllite >>> "
    if not isinstance(text, str):
        text = ('%s'%text).decode('ascii')
    if print_it:
        print("%s%s"%(prefix, text.replace("\n", "\n"+prefix)))


def print_v(text):
    """
    Print a message preceded by neuromllite always
    """
    print_(text, True)


class Base(object):
    """
    Base class of any element (not yet with id)
    """

    def __init__(self, **kwargs):

        self.__dict__['fields'] = collections.OrderedDict()
        self.__dict__['children'] = collections.OrderedDict()

        for name, value in kwargs.items():
            if verbose: print_v(' >  - Init of %s:  %s = %s'%(self.get_type(),name, value))

            if name in self.allowed_fields:

                if self._is_base_type(self.allowed_fields[name][1]):
                    self.fields[name] = (self.allowed_fields[name][1])(value)
                else:
                    self.fields[name] = value
            else:
                info = 'Error, cannot set %s = %s in %s. Allowed fields here:'%(name, value, self.get_type())
                for af in self.allowed_fields:
                    info += '\n  %s %s'%(af, self.allowed_fields[af])

                raise Exception(info)

    # Will be overridden when id required
    def get_id(self):
        return None


    def get_type(self):
        return self.__class__.__name__


    def __getattr__(self, name):

        if verbose: print_v(" > Checking the value of attribute %s in %s..."%(name,self.get_id()))

        if name=='id' and not 'id' in self.allowed_fields:
            return None

        if name in self.__dict__:
            return self.__dict__[name]

        if name=='allowed_fields':
            self.__dict__['allowed_fields'] = collections.OrderedDict()
            return self.__dict__['allowed_fields']

        if name=='allowed_children':
            self.__dict__['allowed_children'] = collections.OrderedDict()
            return self.__dict__['allowed_children']

        if name in self.allowed_fields:
            if not name in self.fields:
                return None
            return self.fields[name]

        if name in self.allowed_children:
            if not name in self.children:
                self.children[name] = []
            return self.children[name]

        print_v('No field or child: %s in %s'%(name, self.id))
        return None


    def _is_base_type(self, value, can_be_list=False):
        return value==int or \
               value==str or \
               value==float or \
               (can_be_list and value==list)

    def __setattr__(self, name, value):

        if verbose: print_v(" > Setting attr %s=%s..."%(name, value))

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


    def to_simple_dict(self):

        d = OrderedDict()
        if verbose: print(' ====   todict: [%s]'%self)
        if len(self.fields)>0:
            for a in self.allowed_fields:
                if a != 'id':
                    if a in self.fields:
                        if verbose: print('  - a: %s = %s (%s)'%(a,self.fields[a],type(self.fields[a])))
                        if self._is_base_type(type(self.fields[a]), can_be_list=True):
                               d[a] = self.fields[a]
                        elif type(self.fields[a])==dict:
                            d[a] = OrderedDict()
                            for b in self.fields[a]:
                                if verbose: print(' - b: %s to %s (%s)'%(b,self.fields[a][b],type(self.fields[a][b])))
                                if self._is_base_type(type(self.fields[a][b]), can_be_list=True):
                                    d[a][b] = self.fields[a][b]
                                elif type(self.fields[a][b])==dict:
                                    d[a][b] = OrderedDict()
                                    for c in self.fields[a][b]:
                                        if verbose: print('  - c: %s = [%s] (%s)'%(c,self.fields[a][b][c], type(self.fields[a][b][c])))

                                        if self._is_base_type(type(self.fields[a][b][c]), can_be_list=True):
                                            d[a][b][c] = self.fields[a][b][c]
                                        else:
                                            d[a][b][c] = self.fields[a][b][c].to_simple_dict()
                                else:
                                    d[a][b] = self.fields[a][b].to_simple_dict()
                        else:
                            d[a] = self.fields[a].to_simple_dict()

        for c in self.allowed_children:
            if c in self.children:
                if len(self.children[c])>0:
                    d[c] = {}
                    for cc in self.children[c]:
                        dd = cc.to_simple_dict()
                        for e in dd: d[c][e] = dd[e]
        if self.id:
            all = OrderedDict({self.id: d})
        else:
            all = d

        return all


    def to_json(self, pre_indent='', indent='    ', wrap=True):

        d = self.to_simple_dict()
        import pprint
        pp = pprint.PrettyPrinter(depth=80)
        if verbose:
            print('Converted to dict:')
            pp.pprint(dict(d))
        ret = pre_indent+json.dumps(d,indent=len(indent))
        if verbose: print("OD to json: [%s]"%ret)

        '''

        if verbose: print_v(' > Converting to JSON: %s, id: %s, fields: %s, children: %s, (wrapping: %s)'%(self.get_type(),self.get_id(), len(self.fields), len(self.children), wrap))

        if len(self.children)==0 and (len(self.fields)==1 and list(self.fields.keys())[0]=='id'):
            raise Exception('Error! %s (type: %s) has no set fields (besides id) or children, and so cannot (currently) be exported to JSON'%(self.id,self.get_type()))

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
                if len(self.children[c])>0:
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
            print_v(" > ")
            print_v(" > =========== pre <%s> ============="%self)
            print_v("------\n%s\n------"%s)

        if wrap:
            try:
                yy = json.loads(s, object_pairs_hook=OrderedDict)
                ret = json.dumps(yy,indent=4)
            except Exception as e:
                print_v('Error loading string as JSON: <%s>'%s)
                raise e

            if verbose:
                print_v(" > ============ json ============")
                print_v(" > %s"%yy)
                print_v(" > ============ post ============")
                print_v(" > %s"%ret)
                print_v(" > ==============================")
        else:
            ret= s

        '''

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
                if len(self.children[c])>0:
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


if __name__ == '__main__':

    # Some tests

    class Network(BaseWithId):

        def __init__(self, **kwargs):

            self.allowed_children = collections.OrderedDict([('cells',('The cell definitions...',Cell)),
                                     ('synapses',('The synapse definitions...',Synapse))])

            self.allowed_fields = collections.OrderedDict([('version',('Information on verson of NeuroMLlite',str)),
                                                           ('seed',('Seed for random number generator used when building network',int)),
                                                           ('random_connectivity',('Use random connectivity',RandomConnectivity))])

            super(Network, self).__init__(**kwargs)

            self.version = 'NeuroMLlite XXX'

    class Cell(BaseWithId):

        def __init__(self, **kwargs):

            self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file',str))])

            super(Cell, self).__init__(**kwargs)

    class Synapse(BaseWithId):

        def __init__(self, **kwargs):

            self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file',str))])

            super(Cell, self).__init__(**kwargs)



    class EvaluableExpression(str):

        def __init__(self,expr):
            self.expr = expr

    class RandomConnectivity(Base):

        def __init__(self, **kwargs):

            self.allowed_fields = collections.OrderedDict([('probability',('Random probability of connection',EvaluableExpression))])

            super(RandomConnectivity, self).__init__(**kwargs)

    net = Network(id='netid')
    cell = Cell(id='cellid')
    cell.neuroml2_source_file = 'nnn'
    cell2 = Cell(id='cellid2')
    cell2.neuroml2_source_file = 'nnn2'
    #net.cells.append(cell)

    print(net)
    print(net.cells)
    print(net)
    '''
    net.cells.append(cell)

    net.cells.append(cell2)
    '''
    rc = RandomConnectivity(probability=0.01)
    net.random_connectivity = rc
    print(rc)
    print(net)

    #print(net['cells'])
    try:
        print(net.notcells)
    except Exception as e:
        print('  As expected, an exception: [%s]...'%e)

    import pprint
    pp = pprint.PrettyPrinter(depth=4)
    d = net.to_simple_dict()
    print(d)
    pp.pprint(dict(d))

    print(net.to_json())
    filename = '%s.json'%net.id
    net.to_json_file(filename)

    from neuromllite.utils import load_json, _parse_element
    data = load_json(filename)
    print_v("Loaded network specification from %s"%filename)
    net2 = Network()
    net2 = _parse_element(data, net2)

    verbose = False
    print('----- Before -----')
    print(net)
    print('----- After -----')
    print(net2)
