class AttributeDict(dict):
    """A dictionary whose items can be accessed as attributes. Be careful not
       to include attributes with names that are dictionary methods:
       'clear', 'copy', 'fromkeys', 'get', 'has_key',
       'items','iteritems', 'iterkeys', 'itervalues', 'keys', 'pop',
       'popitem', 'setdefault', 'update', 'values'
    """

    def __init__(self, **kw):
        "Initialize like a dictionary."
        dict.__init__(self, **kw)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError("No attribute %s" % name)

    def __setattr__(self, name, value):
        "Convert an attribute set into a key set."
        self[name] = value

    def __delattr__(self, name):
        "Delete an attribute using the dictionary."
        try:
            del self[name]
        except KeyError:
            raise AttributeError('No attribute %s' % name)

    def __repr__(self):
        _repr = "AttributeDict(\n"
        for key in sorted(self.keys()):
            _repr += " %s = %r,\n" % (key, self[key])
        _repr += ")"
        return _repr

    def __str__(self):
        "Prints the attributes in alphabetical order."
        _str = ''
        for key in (k for k in sorted(self.keys()) if not k.startswith('_')):
            _str += "%s = %s,\n" % (key, self[key])
        return _str

if __name__ == "__main__":
    d = AttributeDict(a=1, b=2)
    assert d.a == 1
    assert d.b == 2
    d.c = 3
    assert d['c'] == 3
    del d.b
    print(d)
