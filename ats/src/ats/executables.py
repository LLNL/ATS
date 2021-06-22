from atsut import is_valid_executable
from configuration import machine

class Executable(object):
    """Information about an executable to use. Can be created from string or
     list of strings."""
    def __init__ (self, value):
        if isinstance(value, (str, unicode)):
            self.commandList = machine.split(value)
        else:
            self.commandList = value[:]
        self.path = self.commandList[0]

    def is_valid(self):
        "Is this executable valid?"
        if not self.path: return False
        return is_valid_executable(self.path)

    def __str__ (self):
        return " ".join(self.commandList)

    def __repr__ (self):
        return "Executable ('%s')" % str(self)
