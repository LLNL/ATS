"""
Created on Oct 22, 2014

@author: reynolds12

Various base classes
"""

__all__ = ['NoNewFields', 'DebugFields']

import logs
import pprint

#-----------------------------------------------------------------------------          
class NoNewFields(object):
    """Once the fields are set in __init__, setting a new field will raise
    AttributeError.

    To specify your fields, override _names with a tuple listing the field names,
    e.g. _names = ('a', 'b', 'c').
    To initialize the fields to other than None, override _fieldDefault.
    """        
    _fieldNames = ()
    _fieldDefault = None

    def __init__(self, *args, **kwargs):
        self._addFields()
        self.__setPositionalFields(args)
        self.__setKeywordFields(kwargs)

    def _addFields(self):
        for name in self._fieldNames:
            object.__setattr__(self, name, self._fieldDefault)
            
    def __setPositionalFields(self, args):
        nameIter = iter(self._fieldNames)
        for value in args:
            try:
                name = nameIter.next()
                self.__setattr__(name, value)
            except StopIteration:
                raise AttributeError, \
                    'Too many positional args initialzing %s object.  Expected %s, but got %s.' %\
                    (self.__class__, len(self._fieldNames), len(args))

    def __setKeywordFields(self, kwargs):
        for name, value in kwargs.iteritems():
            self.__setattr__(name, value)
        
    def __setattr__(self, name, value):
        if name not in self.__dict__:
            raise AttributeError, \
                'Field "%s" not found in "%s" object.' % (name, self.__class__)
        else:
            object.__setattr__(self, name, value)
            
#-----------------------------------------------------------------------------          
class DebugFields(object):
    """Adds PrettyPrinter behavior to classes.
    """
    #classwide indent, when setIndent has not been called:
    _indent = 0
    def __repr__(self):
        return '%s:\n%s' % (self.__class__, 
                            pprint.PrettyPrinter(indent = self._indent).
                            pformat(self.__dict__))
        
    def setIndent(self, indent):
        # Sets indent for individual instance:
        self._indent = indent
        
#-----------------------------------------------------------------------------          
def demoNoNewFields():
    print("")
    logger = logs.getLogger('demoNoNewFields')
    # Using DebugFields to log class instances below:
    class XY(NoNewFields, DebugFields):
        _fieldNames = ('x', 'y')
        _fieldDefault = 99
        
    foo = XY()    
    logger.info ("foo: %r" % foo)
    foo.x = 17
    logger.info ("foo: %r" % foo)
    try:
        foo.z = 18
    except AttributeError as x:
        logger.info ("Got expected AttributeError:\n'%s'" % str(x)) 

    bar = XY(1,2)
    logger.info ("bar: %r" % bar)
    bar = XY(1)
    logger.info ("bar: %r" % bar)
    bar = XY()
    logger.info ("bar: %r" % bar)
    try:
        bar = XY (1,2,3)
    except AttributeError as x:
        logger.info ("Got expected AttributeError:\n'%s'" % str(x))
    
    bat = XY(x=1, y=2)
    logger.info ("bat: %r" % bat)
    bat = XY(y=2)
    logger.info ("bat: %r" % bat)
    bat = XY(x=1)
    logger.info ("bat: %r" % bat)
    try:
        bat = XY(x=1, y=2, z=3)
    except AttributeError as x:
        logger.info ("Got expected AttributeError:\n'%s'" % str(x))
            
if __name__ == '__main__':
    demoNoNewFields()
