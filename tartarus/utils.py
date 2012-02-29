import inspect

def config(target, **kwargs):
    for k, v in kwargs.items():
        setattr(target, k, v)
    return target


def set_attributes_to_inner_classes(outer, attributes=None, parent=object):
    inner_classes = [member for name, member in inspect.getmembers(outer, inspect.isclass) if issubclass(member, parent)]
    if attributes is None:
        attributes = [k for k, v in inspect.getmembers(outer) if not inspect.ismethod(k) and not inspect.isclass(k)]
    for attr in attributes:
        if hasattr(outer, attr):
            for ic in inner_classes:
                setattr(ic, attr, getattr(outer, attr))
                
                

def get_leaf_subclasses(base, ignore=[], filter=None, attribute='is_usable'):
    leafs=[]
    for c in base.__subclasses__():
        if c not in ignore:
            ignore.append(c)
            if c not in leafs:
                is_leaf = True
                if filter:
                    is_leaf = filter(c)
                if is_leaf and attribute and hasattr(c, attribute):
                    is_leaf = getattr(c, attribute)
                elif is_leaf:
                    is_leaf = not c.__subclasses__()
                if is_leaf:
                    leafs.append(c)
                else:
                    leafs += get_leaf_subclasses(c, ignore)
    return leafs
            
            
            
