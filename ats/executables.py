from ats.atsut import is_valid_executable

class Executable:
    """Information about an executable to use. Can be created from string or
     list of strings."""
    def __init__ (self, value):
        from ats.configuration import machine
        if isinstance(value, str):
            self.commandList = machine.split(value)
        else:
            self.commandList = value.copy()
        self.path = self.commandList[0]

    def is_valid(self):
        "Is this executable valid?"
        return bool(self.path and is_valid_executable(self.path))

    def __str__ (self):
        return " ".join(self.commandList)

    def __repr__ (self):
        return f"Executable('{str(self)}')"
