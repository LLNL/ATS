"""
Created on Oct 22, 2014

@author: reynolds12

Logging and debug support
"""

import logging
import pprint
import sys

__all__ = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL',
           'alignedDecimalFormatter', 'stdoutHandler', 'getLogger',
           'ScopeLoggers', 'DebugFields')

DEBUG    = logging.DEBUG
INFO     = logging.INFO
WARNING  = logging.WARNING
ERROR    = logging.ERROR
CRITICAL = logging.CRITICAL

logging.addLevelName(DEBUG,    "$$$")
logging.addLevelName(INFO,     "---")
logging.addLevelName(WARNING,  "!!!") # This is NOT a to-do item.
logging.addLevelName(ERROR,    "***")
logging.addLevelName(CRITICAL, "@@@")

# Lines up messages (makes level names all 8 wide) and puts "." before fractional
# seconds instead of ",":
alignedDecimalFormatter = logging.Formatter \
    (fmt='%(asctime)19s.%(msecs).03d %(levelname)s %(module)s.%(funcName)s: %(message)s',
     datefmt='%Y-%m-%d %H:%M:%S')
stdoutHandler = logging.StreamHandler(sys.stdout)
stdoutHandler.setFormatter(alignedDecimalFormatter)
# Handles anything up to DEBUG passed to it from a logger:
stdoutHandler.setLevel(logging.DEBUG)


def getLogger(name):
    """ Returns a logger with alignedDecimalFormatter, which logs everything
    up to INFO
    """
    result = logging.getLogger(name)
    result.addHandler(stdoutHandler)
    result.setLevel(logging.INFO)
    """Calling the default logger (e.g. "logging.info") causes a lazy init of the
    root logger and
    its handler, which subsequently sends all but debug messages to stderr.
    If you call the default logger and afterwards call a
    specific logger, the later messages will be output twice - once by the specific
    logger's handler, and once by the root logger's handler.  To prevent this,
    set propagate on this logger to False:
    """
    result.propagate = False
    return result

# For debugging this module:
# def printFrame(frame, msg):
#     print (msg)
#     print ("    File: %s" % frame.f_code.co_filename)
#     print ("    Line: %i" % frame.f_lineno)
#     print ("    Code: %s" % frame.f_code.co_name)
#     print ("    Defined in: %s " % inspect.getmodule(frame))

#-----------------------------------------------------------------------------
import inspect
class ScopeLoggers(logging.LoggerAdapter):
    """ Provides automatic logging of scope entry and exit.

    Uses __init__ and __del__ to do the logging. Object destruction (which calls
    __del__) has always been observed to occur at scope exit, but this is not
    guaranteed by Python.

    Inherits from LoggerAdapter so it can override process(self, msg, kwargs)
    """
    _indent = 0

    def __init__(self, logger, callerContext, parms=""):
        """Log caller entry at creation time and indent"""
        logging.LoggerAdapter.__init__(self, logger, extra=None)
        self.caller = (callerContext + '.' +
                       inspect.currentframe().f_back.f_code.co_name +
                       '(' + parms + ')')
        self.debug((self.__class__._indent * ' ') + '=> ' + self.caller + ' BEGIN')
        self.__class__._indent += 1
        # For debugging this module:
#         thisFrame = inspect.currentframe()
#         lastFrame = thisFrame.f_back
#         printFrame(thisFrame, "This frame:")
#         printFrame(lastFrame, "Calling frame:")
#         print (__name__)

#     def process(self, msg, kwargs):
#         """
#         Overrides logging.LoggerAdapter.process
#
#         replaces funcNames __init__ and __del__ with self.caller:
#         """
#         kwargs["extra"] = dict(kwargs, funcName = self.caller)
#         return msg, kwargs

    def __del__(self):
        """Log caller exit at destruct time and un-indent"""
        self.__class__._indent -= 1
        self.debug((self.__class__._indent * ' ') + ' <= ' + self.caller + ' END')
        # LoggerAdapter doesn't have __del__ in Python 2.6 (old style class) so don't call it:
#         super(ScopeLoggers, self).__del__()

#-----------------------------------------------------------------------------
def demoCallLogger(logger):
    print("")
    logger.debug ("Debug message")
    logger.info ("Info message")
    logger.warning ("Warning message")
    logger.error ("Error message")
    logger.critical ("Critical message")

    logger.info ("BEFORE calling logging.debug. Debug message should appear "
                 "somewhere (sent to stderr with prefix '$$$:root:').")
    logging.basicConfig(level=DEBUG)
    logging.debug("Debug message from root logger")
    logger.info ("AFTER calling logging.debug (this message should appear only once)")

def demoScopeLogger(logger):
    print("")
    _scopeLogger = ScopeLoggers(logger, __name__)
    localLogger = getLogger(__name__)
    localLogger.setLevel(DEBUG)
    localLogger.debug ("Inside " + inspect.currentframe().f_code.co_name)

def demoScopeLoggerParms(logger):
    print("")
    _scopeLogger = ScopeLoggers(logger, __name__, "a=1, b=2")

def demoCaller(logger):
    print("")
    logger.info ('\nlogger.findCaller = "%s"' % str(logger.findCaller()))

def demoLogRecord(logger):
    print("")
    class DictFilter(logging.Filter):
        def filter (self, record):
            sortedDict=record.__dict__.items()
            sortedDict.sort()
            print("record.__dict__ = %s" % str(sortedDict).replace("('", "\n ('") )
            return True
    logger.debug('LogRecord dict below, with added context = "BAR".')
    print("Adding filter")
    logger.addFilter(DictFilter())
    print("Done adding filter")
    logger.debug('This log call caused the filter to put out the dict above.', extra=dict(context="BAR"))

def demoLoggerAdapter(logger):
    print("")
    class PLogger(logging.LoggerAdapter): None
#             # @override
#             def process(self, msg, kwargs):
#                 kwargs["extra"] = self.extra
#                 return ('(PLogger self.extra["context"] = %s): %s' %
#                         (str(self.extra["context"]), msg),
#                         kwargs)
    pLogger = PLogger(logger, dict(context="BAR"))
    pLogger.info("Here we are.")

def demoLogging():
    demoLogger = getLogger(__name__)
    demoLogger.setLevel(DEBUG)
    demoCallLogger(demoLogger)
    demoScopeLogger(demoLogger)
    demoScopeLoggerParms(demoLogger)
    demoCaller(demoLogger)
    demoLogRecord(demoLogger)
    demoLoggerAdapter(demoLogger)

#-----------------------------------------------------------------------------
class DebugFields(object):
    """Adds PrettyPrinter behavior to classes.
    """
    #classwide indent, when setIndent has not been called:
    _indent = 0
    def __repr__(self):
        return '%s:\n%s' % (self.__class__,
                            pprint.PrettyPrinter(indent = self._indent).pformat(self.__dict__))

    def setIndent(self, indent):
        # Sets indent for individual instance:
        self._indent = indent

def demoDebugFields():
    print("")
    logger = getLogger('demoDebugFields')
    logger.setLevel(DEBUG)
    instance1 = DebugFields()
    instance1.field1 = 1
    instance1.field2 = "two"
    instance1.field3 = ('a', 'b', 'c')
    instance1.field4 = {'x' : 8, 'y' : 9, 'z' : 10}
# Causes infinite loop.  Depth doesn't work, since recursion is within __repr__,
#  not within pprint
#     instance1.field5 = instance1
    logger.debug('instance1 __repr__()output: %r' % instance1)
    logger.debug('instance1 pformat output: %s' % pprint.PrettyPrinter().pformat(instance1))
    instance1.setIndent(4)
    logger.info ("instance1 indented output: %r" % instance1)

# Exploring special names:
#         self._debugVars\
#             (("__file__",
#               "__name__",
#               "__package__",
#               "self.__module__",
#               "self.__class__"))
#
#     def _debugVars(self, varNames):
#         varsString = ''
#         for varName in varNames:
#             value = eval('str(%s)' % varName)
#             line = '%20s = "%s"' % (varName, value)
#             varsString += '\n' + line
#         self.logger.debug(varsString)
#
#     def _debugVar(self, var):
#         value = eval('str(%s)' % var)
#         self.logger.debug ('%s = "%s"' % (var, value))
#

if __name__ == '__main__':
    demoLogging()
    demoDebugFields()
