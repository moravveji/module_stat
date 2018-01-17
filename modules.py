"""
Author: Ehsan Moravveji
Date:   09 January 2018
Purpose: This module manipulates the loaded modules in the users' .pbs job scripts
"""

import sys, os, glob
import logging

##########################################################################
logger = logging.getLogger(__name__)
##########################################################################
 
class module:
  """
  A class to manipulate the modules loaded job script.
  Tip: wrap the instantiation through a try/except block to capture the FileNotFoundError.
  """
  #---------------------
  def __init__(self, file_sc):
    """
    Constructor

    @param file_sc: full path to the original .pbs script, with extension .SC
    @type file_sc: str
    """
    if not os.path.exists(file_sc):
      logger.error('__init__: "{0}" does not exist.'.format(file_sc))
      raise FileNotFoundError
    self.file_sc   = file_sc # script source file
 
    # The file content as a list of strings
    self.lines     = None
   
    # The information that we want to extract from each file
    self.toolchain = 2014    # default to 2014
    # default: empty dict. when filled up the key will be module name; 
    # if the version is specified, that will be the value, else value is None
    self.loaded    = dict()  
   
    # Start manipulating the .SC script file
    self.__read()
    self.__find_toolchain()
    self.__find_module_load()

  #---------------------
  def __read(self):
    """
    Reads the file once, and stores the file content as a list of strings
    (one item per line) for further manipulation
    """
    with open(self.file_sc, 'r') as r: self.lines = r.readlines()

  #---------------------
  def __find_toolchain(self):
    """
    Find the line which switches the toolchain, e.g. 
    "source switch_to_2015a" 
    """
    if self.lines is None: 
      logger.warning('find_toolchain: The script file is not read yet')
      return

    for line in self.lines:
      if 'source switch_to_201' in line:
        line = line.rstrip('\r\n')
        self.__set_toolchain(line)
      elif 'module use /apps/leuven/' in line:
        line = line.rstrip('\r\n')
        self.__set_toolchain(line)
      else:
        pass

  #---------------------
  def __find_module_load(self):
    """
    Reads and scans the in the document.
    """
    if self.lines is None: 
      logger.warning('find_module_load: The script file is not read yet')
      return

    for line in self.lines:
      if line.strip().startswith('module load'):
        self.__add_module(line)
    
  #---------------------
  def __add_module(self, mod):
    """
    Add another module to the dictionary of self.loaded modules
    Note, if the passed module name (mod) contains the specific version of the 
    module (e.g. Matlab/R2017b), then, the module name is used as the key, and 
    the version is set to the version. If the specific version is missing, then,
    the value is set to "None".

    @param mod: the name of the module to add
    @type mod: str
    """
    mod = mod.replace('module load', '').strip()
    if "/" in mod: 
      key, val = mod.split("/")
    else:
      key, val = mod, None

    # update
    self.loaded[key] = val

  #---------------------
  def __set_toolchain(self, toolchain):
    """
    Set the toolchain other than the default 2014, provided the user has explicitly
    sourced a specific toolchain. This phrase is passed in the string: toolchain

    @param toolchain: the toolchain string which looks like the following example:
           toolchain = 'source switch_to_2015a'. From this, we extract 2015 as an 
           integer, and assign it to self.toolchain
    @type toolchain: str
    """
    toolchain = toolchain.strip()
    check_1 = 'source switch_to_201' in toolchain
    check_2 = 'module use /apps/leuven' in toolchain
    OK      = all([check_1, check_2])
    if not OK:
      logger.warning('set_toolchain: wrong string is provided')
      return
    if check_1: year = int(toolchain[17:21])
    if check_2: year = int(toolchain.split('/')[4][:-1])

    self.toolchain = year
    
  #---------------------

##########################################################################

