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


    @classmethod
    def _is_base_type(cls, value, can_be_list=False):
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


    @classmethod
    def to_dict_format(cls, var, ordered = True):

        if verbose: print(' ====   to_dict_format: [%s]'%var)
        if cls._is_base_type(type(var)): # e.g. into float, str
            return var
        elif type(var) == list:
            l = []
            for v in var:
                l.append(cls.to_dict_format(v, ordered=ordered))
            return l
        elif type(var) == dict:
            d = OrderedDict() if ordered else {}
            for k in var:
                d[k] = cls.to_dict_format(var[k], ordered=ordered)
            return d

        else:  # assume a type Base

            d = OrderedDict() if ordered else {}

            if len(var.fields)>0:
                for field_name in var.allowed_fields:
                    if field_name != 'id':
                        if field_name in var.fields:
                            if verbose: print('  - field_name: %s = %s (%s)'%(field_name,var.fields[field_name],type(var.fields[field_name])))
                            d[field_name] = cls.to_dict_format(var.fields[field_name], ordered=ordered)

            for child_name in var.allowed_children:
                if child_name in var.children:
                    if len(var.children[child_name])>0:
                        d[child_name] = OrderedDict() if ordered else {}
                        for child in var.children[child_name]:
                            dchild = cls.to_dict_format(child, ordered=ordered)
                            for k in dchild:
                                d[child_name][k] = dchild[k]
            if var.id:
                d = OrderedDict({var.id: d}) if ordered else {var.id: d}
            return d



    def to_json(self, indent='    '):

        d = Base.to_dict_format(self)
        import pprint
        pp = pprint.PrettyPrinter(depth=80)
        if verbose:
            print('Converted to dict:')
            pp.pprint(dict(d))
        ret = json.dumps(d,indent=len(indent))
        if verbose: print("OD to json: [%s]"%ret)

        return ret

    def to_yaml(self, indent='    '):

        import yaml
        d = Base.to_dict_format(self, ordered=False)
        import pprint
        pp = pprint.PrettyPrinter(depth=80)
        if verbose:
            print('Converted to dict:')
            pp.pprint(dict(d))
        ret = yaml.dump(d,indent=len(indent),sort_keys=False)
        if verbose: print("OD to yaml: [%s]"%ret)

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
        with open(file_name,'w') as f:
            f.write(self.to_json())
        print_v("Written NeuroMLlite %s to: %s"%(self.__class__.__name__, file_name))
        return file_name

    def to_yaml_file(self, file_name=None):
        if not file_name:
            file_name='%s.yaml'%self.id
        with open(file_name,'w') as f:
            f.write(self.to_yaml())
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

            self.version = 'NeuroMLlite 0.0'

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
    cell = Cell(id='cellid1')
    cell.neuroml2_source_file = 'nnn'
    cell2 = Cell(id='cellid2')
    cell2.neuroml2_source_file = 'nnn2'
    #net.cells.append(cell)

    print(net)
    print(net.cells)
    print(net)
    '''  '''
    net.cells.append(cell)
    net.cells.append(cell2)

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
    #d0 = net.to_simple_dict()
    #print(d0)
    print('--- new format ---')
    d = Base.to_dict_format(net)
    print(d)
    pp.pprint(dict(d))
    print('  To JSON:')
    print(net.to_json())
    print('  To YAML:')
    print(net.to_yaml())

    filenamej = '%s.json'%net.id
    net.to_json_file(filenamej)

    filenamey = '%s.yaml'%net.id
    net.id = net.id+'_yaml'
    net.to_yaml_file(filenamey)
    from neuromllite.utils import load_json, load_yaml, _parse_element

    dataj = load_json(filenamej)
    print_v("Loaded network specification from %s"%filenamej)
    netj = Network()
    _parse_element(dataj, netj)

    datay = load_yaml(filenamey)
    print_v("Loaded network specification from %s"%filenamey)

    nety = Network()
    _parse_element(datay, nety)

    verbose = False
    print('----- Before -----')
    print(net)
    print('----- After via %s -----'%filenamej)
    print(netj)
    print('----- After via %s -----'%filenamey)
    print(nety)
