"""
Author: Ehsan Moravveji
Date:   11 January 2018
Purpose: This module provides a container for the statistics of the modules used in PBS scripts. 
        A potentially interesting attribute of the "stats" class is the version_counter dictionary
        whose keys contain the full trace of a module (toolchain, software name and version), and 
        the values count the number of times that module has been loaded in all scripts.
"""
import sys, os, glob
import logging
import numpy as np

##########################################################################
logger = logging.getLogger(__name__)
##########################################################################

class stats:
  """
  This class collects the statistics of the resource requirements of a job and the 
  modules/toolchain used. This is useful for visualization 
  """
  def __init__(self):
    """
    Constructor
    Available attributes:
    + avail_toolchain: lists the toolchain year of the modules on the cluster (integer)
    + avail_modules: dictionary with toolchain year as keys (integer), and a string list of 
                     module name/version as value. E.g. 
                     self.avail_modules[2015] = {..., 'Java/1.8.0_31', ...}
    + module_counter:  counter dictionary with keys in the format consisting of the module name
                     and the values enumerating the total number of times this specific module
                     is loaded, regardless of whichever version or toolchain it belongs to. E.g.
                     self.module_counter = {..., 'Java': 307, ...}
    + version_counter: counter dictionary with keys in the format 'year/module/version', 
                     and the values enumerating the total number of times this specific
                     module is loaded. E.g.
                     self.version_counter = {..., '2015/Java/1.8.0_31': 123, ...}
    """
    self.avail_toolchain = [2014, 2015, 2016]
    self.avail_modules   = {toolchain: list() for toolchain in self.avail_toolchain}
    self.module_counter  = dict()
    self.version_counter = dict()

    # Allocate the attributes above
    self.__set_avail_modules()
    self.__set_dic_module_counter()
    self.__set_dic_version_counter()

  #---------------------
  def __enter__(self):
    return self

  #---------------------
  def __exit__(self, type, value, traceback):
    pass

  #---------------------
  def get_avail_modules(self, toolchain):
    """
    Searches for available modules to the users inside the path: 
    /apps/leuven/thinking/{toolchain}a/modules/all
    where the {toolchain} will be replaced with a string representation of the passed toolchain
    In return, a list is returned that contains the full module name and version name(s) of that
    module, for all possible modules. E.g. if within the 2014 toolchain, there are 6 different 
    Python modules, the return list will contain:
    [..., 'Python/2.7.11-foss-2014a', 'Python/3.2.5-intel-2014a', ...]

    @param toolchain: the toolchain year
    @type toolchain: int
    @return: list of modules and their different versions (if available) for a specific toolchain
    @rtype: list
    """
    if toolchain not in self.avail_toolchain:
      logger.warning('get_avail_modules: toolchain year {0} is invalid'.format(toolchain))
      raise ValueError

    avail = []
    path  = '/apps/leuven/thinking/{0}a/modules/all'.format(toolchain)
    for dirpath, dirnames, filenames in os.walk(top=path, topdown=True, followlinks=False):
      software = os.path.basename(dirpath)
      if filenames:
        for version in filenames:
          if '~' in version: continue
          soft_ver = '{0}/{1}'.format(software, version)
          avail.append(soft_ver)  # when software has a version(s)
      else: 
        avail.append(software)    # when a software has no version

    return avail

  #---------------------
  def __set_avail_modules(self):
    """
    Sets the list of available modules for all available toolchains
    """
    for toolchain in self.avail_toolchain:
      self.avail_modules[toolchain] = self.get_avail_modules(toolchain)

  #---------------------
  def get_dic_version_counter(self):
    """
    Returns a (rather big) dictionary with keys consisting of the module toolchain plus 
    module name and version, and values defaulting to 0. Then, for every use/load of a module, 
    the counter/value can be incremented by one.
    E.g. one of the items of returned dictionary would look like:
    {..., '2016/OpenBLAS/0.2.15-GCC-4.9.3-2.25-LAPACK-3.6.0': 0, ...}
    You may compare this with the other method get_dic_module_counter().
    
    @return: key/value pairs where the keys are the full module names (year, software, version,
             seperated by slash), and the values default to zero.
    @rtype: dict
    """
    dic = dict()
    for toolchain, avail_modules in self.avail_modules.items():
      for avail_module in avail_modules:
        dic['{0}/{1}'.format(toolchain, avail_module)] = 0

    return dic

  #---------------------
  def __set_dic_version_counter(self):
    """
    This method just calls the get_dic_version_counter(), and sets the self.version_counter attribute
    """
    self.version_counter = self.get_dic_version_counter()

  #---------------------
  def get_dic_module_counter(self):
    """
    Returns a dictionary with keys consisting of the module name (excluding toolchain year and the
    version number), and values defaulting to 0. For every use/load of a module, the counter/value 
    can be incremented by one.
    E.g. one of the items of returned dictionary would look like:
    {..., 'OpenBLAS': 0, ...}.
    You may compare this with the other method get_dic_version_counter().

    @return: key/value pairs where the keys are just the module names and the values default 
             to zero.
    @rtype: dict
    """
    dic = dict()
    for toolchain, avail_modules in self.avail_modules.items():
      for module in avail_modules:
        key = module.split('/')[0] if '/' in module else module
        dic[key] = 0
     
    return dic

  #---------------------
  def __set_dic_module_counter(self):
    """
    This method just calls the get_dic_module_counter(), and sets the default self.module_counter attribute
    """
    self.module_counter = self.get_dic_module_counter()

  #---------------------
  def increment_version_count(self, toolchain, module, version):
    """
    x
    """
    if version is None:
      key = '{0}/{1}'.format(toolchain, module)
    else:
      key = '{0}/{1}/{2}'.format(toolchain, module, verison) 

    if key not in self.version_counter:
      logger.warning('increment_version_counter: key: "{0}" is invalid'.format(key))
      return

    self.version_counter[key] += 1

  #---------------------
  def increment_module_count(self, module):
    """
    x
    """
    if not module in self.module_counter:
      logger.error('increment_module_count: invalid key: {0}'.format(module))
      raise KeyError

    self.module_counter[module] += 1

  #---------------------
  def sort_module_counts(self, showtop=3):
    """
    Filter the most used modules.

    @param showtop: Clip off this number of top modules that were used
    @type showtop: int
    @return: two lists: the first list gives the name of the most counted/used modules, and the 
             2nd list gives the counts. default = 3
    @rtype: tuple 
    """
    if not isinstance(showtop, int):
      logger.error('sort_module_counts: the argument "showtop" must be a positive integer')
      raise ValueError

    if showtop < 1:
      logger.error('sort_module_counts: the argument "showtop" must be a positive integer')
      raise ValueError

    keys = []
    vals = []
    for key, val in self.module_counter.items():
      keys.append(key)
      vals.append(val)
    vals = np.array(vals)
    indx = np.argsort(vals)[::-1]   # Descending
    keys = [keys[i] for i in indx]
    vals = [vals[i] for i in indx]
    
    showtop = len(keys) if len(keys) < showtop else showtop

    return keys[:showtop], vals[:showtop]

  #---------------------
  def write_sort_module_counts_as_ascii(self, showtop=3, filename='modules-ranking.txt'):
    """
    Call sort_module_counts() method and write out the results to an ascii file.
    
    @param showtop: clip off this number of top modules that were loaded. This will be passed
           directy to call sort_module_count() method.
    @type showtop: int
    @param filename: the full path to the output ASCII file.
    @type filename: str
    @return: None
    @rtype: None
    """
    top_keys, top_vals = self.sort_module_counts(showtop=showtop)
    n_top = len(top_keys)
    lines = ['#    Count  Module \n']
    for i in range(n_top):
      lines.append('{0:<4d} {1:<6d} {2:<} \n'.format(i+1, top_vals[i], top_keys[i]))

    with open(filename, 'w') as w: w.writelines(lines)
    logger.info('write_sort_module_counts_as_ascii: Successfully wrote to: {0}'.format(filename))

  #---------------------
  #---------------------
  #---------------------

##########################################################################

