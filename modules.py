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
# Bash-specific commands/wildcards that we skip if in a script file
bash_exclude = ['if', 'then', 'else', 'fi', 'do', 'done', 'case', 'in', 'esac', 
                'export', 'cd', 'cp', 'mv', 'mkdir', 'rm', 'echo', 'hostname', 
                'time']
skip_chars   = set(['-', '$', ';', '*', '"'])

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
    self.called    = dict()
    self.used      = dict()
   
    # Start manipulating the .SC script file
    self.__read()
    self.__find_toolchain()
    self.__find_module_use()

  #---------------------
  def __read(self):
    """
    Reads the file once, and stores the file content as a list of strings
    (one item per line) for further manipulation. Note that all lines starting with 
    the comment character "#" are thrown away
    """
    with open(self.file_sc, 'r') as r: orig = r.readlines()
    self.lines = list()
    for raw in orig:
      if raw.strip().startswith('#'): continue
      self.lines.append(raw.strip())

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
  def __find_module_use(self):
    """
    Reads and scans the in the document.
    """
    if self.lines is None: 
      logger.warning('find_module_use: The script file is not read yet')
      return

    for line in self.lines:
      if line.strip().startswith('module load'):
        self.__add_module(line)
      else:
        self.__check_calls(line)
    self.used = dict(self.loaded, **self.called)
    
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
  def __check_calls(self, line):
    """
    Check if the line might contain a call to an executable. If it might contain a call
    to a module executable, then, the list of words in that line are trimmed off not to contain
    command-line arguments or arguments/variables starting with "$" character. Even after doing 
    that, the list of words passed to __add_calls() method may or maynot contain correct executable
    name(s). E.g. from a line like 
        monitor -l runtime.log -- matlab -nodisplay -nojvm -r "MyExec 1 2 3" 
    we exclude: -l, --, -nodisplay, -nojvm, -r and "MyExec 1 2 3"
    and only capture: monitor, runtime.log and matlab for later processing.
    Note: if the length of the line is only 1, the method ignores it, and 

    @param line: One line of the script file
    @type line: str
    @return: None
    @rtype: None
    """
    words   = line.split() # split by space
    if len(words) == 1: return None

#    first   = words[0]
#    if first in bash_exclude: 
#      pass
#    else:
    maybe = []
    for word in words:
      if word[0] in skip_chars or '=' in word: continue
      maybe.append(word)
    self.__add_calls(maybe)

  #---------------------
  def __add_calls(self, candidates):
    """
    This method extends the self.called attribute by adding extra items to it. The keys are the
    the items in the list, and the values are set to None

    @param candidates: the potential/candidate executable names found in the script files. The
           list is already trimmed from some obvious words after a former call by __check_calls().
    @type candidates: list of strings
    @return: None
    @rtype: None
    """
    for key in candidates: self.called[key] = None

  #---------------------
  #---------------------

##########################################################################

