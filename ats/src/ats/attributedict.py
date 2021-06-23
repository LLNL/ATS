from __future__ import print_function
from cStringIO import StringIO

class AttributeDict (dict):
    """A dictionary whose items can be accessed as attributes. Be careful not to
       include attributes with names that are dictionary methods:
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
            raise AttributeError, "No attribute %s" % name

    def __setattr__(self, name, value):
        "Convert an attribute set into a key set."
        self[name] = value

    def __delattr__(self, name):
        "Delete an attribute using the dictionary."
        try:
            del self[name]
        except KeyError:
            raise AttributeError, 'No attribute %s' % name

    def __repr__(self):
        out = StringIO()
        print("AttributeDict(", file=out)
        keys = self.keys()
        keys.sort()
        for key in keys:
            print("  %s = %r," % (key, self[key]), file=out)
        print(")", file=out)
        s = out.getvalue()
        out.close()
        return s

    def __str__(self):
        "Prints the attributes in alphabetical order."
        out = StringIO()
        keys = self.keys()
        keys.sort()
        for key in keys:
            if key.startswith('_'):
                next
            print >>out, key, " = ", str(self[key])
            print("%s = %s," % (key, self[key]), file=out)
        s = out.getvalue()
        out.close()
        return s

if __name__ == "__main__":
    d=AttributeDict(a=1, b=2)
    assert d.a == 1
    assert d.b == 2
    d.c = 3
    assert d['c'] == 3
    del d.b
    print(d)
