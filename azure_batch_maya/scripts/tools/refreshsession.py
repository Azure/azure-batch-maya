import inspect
import os
import sys

def refreshSessionModules(userPath=None):
    """Remove all loaded modules from the "azure-batch-maya" directory and subdirectories.
    This means any changes to the plugin code can be reloaded without needing to restart Maya.
    """
    if userPath is None:
        # call dirname exactly thrice to get the base "azure-batch-maya" directory
        userPath = os.path.dirname(os.path.dirname(os.path.dirname(inspect.getfile(inspect.currentframe()))))
    userPath = os.path.normpath(userPath.lower())

    toDelete = []
    for key, module in sys.modules.iteritems():
      try:
          moduleFilePath = os.path.normpath(inspect.getfile(module).lower())
          # Don't try and remove the plugin script itself
          if os.path.basename(moduleFilePath) == "azurebatch".lower():
              continue
          
          if (moduleFilePath).startswith(userPath):
              toDelete.append(key)
      except:
          pass
    
    # delete outside the iterator loop to prevent changing the iterator
    for module in toDelete:
        del (sys.modules[module])