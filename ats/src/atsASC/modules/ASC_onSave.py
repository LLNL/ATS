####################################################################################
#
# Module to hold functions for register with the onSave function.
#
####################################################################################

def addMachineInfo( rdict, manager):
  """
  Callback function for manager onSave function.  It adds additional information
  about the machine in the machine AttributeDict in the file created by
  manager.saveResults.
  """
  rdict.machine['npMax'] = manager.machine.npMax
  
####################################################################################


