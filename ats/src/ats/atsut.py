import os, sys
from attributedict import AttributeDict

statuses = AttributeDict()

_StatusCodesAbr = dict(
   CREATED = "INIT",
   INVALID = "INVD",
   PASSED = "PASS",
   FAILED = "FAIL",
   SKIPPED = "SKIP",
   RUNNING = 'EXEC',
   FILTERED = 'FILT',
   TIMEDOUT = 'TIME',
   BATCHED = "BACH",
   HALTED = "HALT",
   EXPECTED = "EXPT",
   LSFERROR = "LSFE",
)
   
class _StatusCode:
    def __init__(self, name):
        self.name = name
        self.abr = _StatusCodesAbr[name]

    def __str__(self):
        return self.abr

    def __eq__(self, other):
        if isinstance(other, _StatusCode):
            return self.name == other.name
        elif isinstance(other, (str, unicode)):
            return self.name == other or self.abr == other
        else:
            return False

    def __ne__(self, other):
        return self.name != other.name

    def __repr__(self):
        return "StatusCode(%s)" % repr(self.name)

def StatusCode(name):
   "Return a status code so that they compare with 'is'. "
   try:
       return statuses[name]
   except KeyError:
       new = _StatusCode(name)
       statuses[name] = new
       return new

CREATED = StatusCode("CREATED")    
INVALID = StatusCode("INVALID")
PASSED = StatusCode("PASSED")
FAILED = StatusCode("FAILED")
SKIPPED = StatusCode("SKIPPED")
RUNNING = StatusCode("RUNNING")
FILTERED = StatusCode("FILTERED")
TIMEDOUT = StatusCode("TIMEDOUT")
BATCHED = StatusCode("BATCHED")
HALTED = StatusCode("HALTED")
EXPECTED = StatusCode("EXPECTED")
LSFERROR = StatusCode("LSFERROR")

class AtsError (Exception):
    "Exception class for Ats."
    def __init__ (self, msg):
        Exception.__init__ (self, msg)

def expandpath (path):
    "Return a normalized, variable and ~-expanded version of path"
    path = str(path)
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    path = os.path.normpath(path)
    return path

def abspath(path):
    "Return an absolute, expanded path."
    return os.path.abspath(expandpath(path))

_debug = 0

def debug(value=None):
    "Return the debug flag; if value given, set it."
    global _debug
    if value is None:
        return _debug
    else:
        _debug = int(value)

def is_valid_file (path):
    "Does path represent a valid file?"
    path = abspath(path)
    return os.path.isfile(path)

def is_valid_executable (path):
    "Does path represent a valid executable?"
    path = abspath(path)
    return is_valid_file(path) and os.access(path, os.X_OK)

if __name__ == "__main__":
    print locals()
