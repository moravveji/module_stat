"""
Author: Ehsan Moravveji
Date:   11 January 2018
Purpose: This module provides a container for the statistics of the modules used in PBS scripts. 
        A potentially interesting attribute of the "stats" class is the version_counter dictionary
        whose keys contain the full trace of a module (toolchain, software name and version), and 
        the values count the number of times that module has been loaded in all scripts.

Examples:
        To instantiate the class
        >>>with stats.stats() as stat:
        >>>  ...

        To write the dictionary of the executables to an ASCII file. This is really advisible 
        once every while, walking through the whole modules and collecting the executables every
        time takes several minutes. 
        >>>stat     = stats.stats()
        >>>stat.write_dic_executables('executables.txt')

        To read the dictionary of the executables from an already-existing ASCII file
        >>>with stats.stats() as stat: dic_exec = stat.read_dic_executables('executables.txt')

        To read the dictionary of the executables, and set self.executables in one go, do
        >>>with stats.stats() as stat:
        >>>  stat.read_and_set_dic_executables('executables.txt')
        >>>  dic_exec = stat.get_dic_executables()

"""
import sys, os, glob
import logging
import subprocess
import numpy as np

##########################################################################
logger = logging.getLogger(__name__)
##########################################################################

class stats:
  """
  This class collects the statistics of the resource requirements of a job and the 
  modules/toolchain used. This is useful for visualization 
  """
  def __init__(self, cluster='thinking', exec_file=None, auto=True):
    """
    Constructor
    Available attributes:
    
    @param cluster: the name of the target cluster which we aim to collect stats.
                    The valid names are (case-insensitive): ThinKing, Cerebro, Genius, Breniac
                    default: ThinKing
    @type cluster: str
    @param exec_file: the name of an ASCII file which contains the list of executables and their
                     corresponding module file, only if the file is already generated and exists.
                     Else, you may live this optional argument as None, and make/provide it later.
                     default: None
    @type exec_file: str 
    @param auto: Automatically apply many methods to fill up the attributes entirely. 
                     Note that this can be very time-consuming. 
                     default: True
    @type auto: bool

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
    + executables:   dictionary which collects the name of the executables of any module (as key)
                     and assigns that to the module name (as the value). This is done by searching
                     into the "bin" folder of the modules folder.
    """
    # Attributes passed to instantiate the class
    self.cluster = cluster.lower()
    self.check_cluster()
    self.executables_file= exec_file
    self.auto = auto

    # Currently available modules/software
    self.avail_toolchain = [2014, 2015, 2016, 2018]
    self.avail_modules   = {toolchain: list() for toolchain in self.avail_toolchain}
    self.executables     = dict()
    self.list_executables= list()

    # Counters
    self.module_counter  = dict()
    self.version_counter = dict()
    
    self.n_max_modules = 0

    # Allocate the attributes above
    if self.auto:
      self.__set_avail_modules()
      self.__set_dic_module_counter()
      self.__set_dic_version_counter()
#    self.__set_dic_executables()
      self.__set_list_executables()

  #---------------------
  def __enter__(self):
    return self

  #---------------------
  def __exit__(self, type, value, traceback):
    pass

  #---------------------
  def setter(self, attr, val):
    """
    Setter method of the class
    @param attr: an available public attribute of the class
    @type attr: str
    @param val: The value for the attribute to be set
    """
    if hasattr(self, attr): 
      setattr(self, attr, val)
    else:
      logger.warning('setter: stats class does not have attribute: {0}'.format(attr))

  #---------------------
  def check_cluster(self):
    try:
      assert self.cluster in ['thinking', 'cerebro', 'genius', 'breniac']
    except AssertionError:
      logger.error('Invalid cluster specified: {0}'.format(self.cluster))
      sys.exit(1)

  #---------------------
  def get_avail_modules(self, toolchain):
    """
    Searches for available modules to the users inside the path: 
    /apps/leuven/{cluster}/{toolchain}a/modules/all
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
    path  = '/apps/leuven/{0}/{1}a/modules/all'.format(self.cluster, toolchain)
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

  # Executables List
  #---------------------
  def __set_list_executables(self):
    """
    Set the attribute self.list_executables by calling the public method get_list_executables().
    """
    if self.list_executables: return # already set, why bother?
    self.list_executables = self.get_list_executables()

  #---------------------
  def get_list_executables(self):
    """
    This method is somehow similar to get_dic_executables(), but returns a list of tuples, instead
    of a dictionary. So, the identical executables (similar names) will not be overwritten anymore.

    Walks through all modules in all toolchains, and searches for the "bin" or "bin64" folder under 
    all possible versions of that software. If the software/module has a "bin/bin64" folder, 
    then, the name of the executable is taken as the key, and name of the module is taken
    as the value of the dictionary. 
    E.g. the "R" package has a "bin" folder (for any of the toolchains and/or versions), and
    inside that, there are two executable files, called "R" and "Rscript". As a result, the
    self.executable dictionary would have two extra items (key/value) pairs as:
    self.executable = {..., 'R': 'R', 'Rscript': 'R', ...}. 

    Note: Two cases happen:
      + case a. The software has a bin/bin64 folder (or both), just right under the version folder
      + case b. The software might have a bin/bin64 (or both), but they are buried under folder
                hierarchy, or there are multiple bin/bin64 folders available for a single version
    We treat both cases here.

    Note: calling this public method takes few minutes, so, one may write the outcome as an ASCII
          file and recycle that file later on. This ASCII file must be updated once in a while.
          For that, see the public method: write_dic_executables()

    @return: list of tuples containing the following elements per each tuple:
          - toolchain: int; gets the toolchain from self.avail_toolchain 
          - module: str; the module name
          - version: str; the version name
          - executable: str: the executable name
    @rtype: list of tuples
    """
    # if self.executables is non-empty, just return its copy
    if self.list_executables:
      return self.list_executables.copy()  # otherwise, a pointer to the list will be returned
    else: 
      pass

    # Thus, below here, self.list_executables is empty
    litup = list() # list of tuples, hence litup

    #%%%%%%%%%%%%%%%%%%
    def print_this(ex, k, v):
      """ just define a local printing convenience function """
      print('{0}: {1}, {2}'.format(ex, k, v))
    #%%%%%%%%%%%%%%%%%%

    def append_to_list(tc, mod, vers, ex):
      """ append the tuple (toolchain, module_name, version_name, exec_name) to the list "litup" """
      flag_tc  = isinstance(tc, int)
      if not flag_tc:
        logger.error('get_list_executables: append_to_list: toolchain must be integer type')
        raise TypeError

      flag_dat = '.dat' in ex
      flag_txt = '.txt' in ex
      flag_so  = '.so'  in ex
      flag_conf= '.conf' in ex or '.config' in ex
      flag_cmd = '.cmd' in ex
      flag_jar = '.jar' in ex
      flag_tar = '.tar' in ex
      flag_gz  = '.gz' in ex
      flag_bat = '.bat' in ex
      flags    = [flag_dat, flag_txt, flag_so, flag_conf, flag_cmd,
                  flag_jar, flag_tar, flag_gz, flag_bat]
      if not any(flags): litup.append( (tc, mod, vers, ex) )

    #%%%%%%%%%%%%%%%%%%

    def parse_exec_files(toolchain, module_name, vers_name, exec_files):
      """  Create a tuple of exec files to append to the list, only if the file is executable """  
      for exec_file in exec_files:
        X_OK = os.access(path=exec_file, mode=os.X_OK, follow_symlinks=True) 
        if not X_OK: continue
        exec_name = os.path.basename(exec_file)
        append_to_list(toolchain, module_name, vers_name, exec_name)

    #%%%%%%%%%%%%%%%%%%

    def find_bindir_recursively(path):
      """ Find bin/bin64 folders recursively under the "path" directory """
      cmnd = 'find {0} -type d \( -name bin -o -name bin64 \)'.format(path)
      proc = subprocess.Popen(cmnd, shell=True, STDOUT=subprocess.PIPE)
      output, err = proc.communicate()
      if not output:
        logger.warning('find_bindir_recursively: found no bin/bin64 folders')






    #%%%%%%%%%%%%%%%%%%

    # exclude modules that have no bin/bin64 folders in them
    exclude = set(['bin', 'accounting', 'intel_env', 'foss_env'])
    for toolchain in self.avail_toolchain:
      path = '/apps/leuven/{0}/{1}a/software'.format(self.cluster, toolchain)
      dirs = glob.glob(path + '/*')

      if len(dirs) == 0:
        logger.error('__set_dic_executables: Found no modules inside {0}'.format(path))
        raise ValueError

      # local counter to stop the for-loop if number of found modules exceeds n_max_modules
      counter = 0


      find_bindir_recursively(path)


      for mod in dirs:
        module_name = os.path.basename(mod)
        if module_name in exclude: continue
        module_vers = glob.glob(mod + '/*')

        for vers in module_vers:
          vers_name = os.path.basename(vers)
          bin_path  = '{0}/bin'.format(vers)
          bin64_path= '{0}/bin64'.format(vers)

          # Case a. The version folder already has bin/bin64 folder
          # executables in bin
          if os.path.exists(bin_path): 
            exec_files = glob.glob(bin_path + '/*')
            # key: exec filename, key: module name
            parse_exec_files(toolchain, module_name, vers_name, exec_files)

          # executables in bin64
          elif os.path.exists(bin64_path):
            exec_files = glob.glob(bin64_path + '/*')
            # key: exec filename; key: module name
            parse_exec_files(toolchain, module_name, vers_name, exec_files)

          # Case b. the bin/bin64 folder is located few levels deeper in the directory tree!
          else: 


#            continue




            # this finds the bin/bin64 folder, and all other junk; so, needs trimming later on
#            maybe_bin_dirs = glob.glob(vers + '/**/bin*', recursive=True)
            maybe_bin_dirs = glob.glob(vers + '/bin*'+os.sep, recursive=True)
       



            if not maybe_bin_dirs: continue # has no bin/bin64 at all
            print('-> bin dir? {0}'.format(maybe_bin_dirs) )
            list_bin_dirs  = []
            for bin_dir in maybe_bin_dirs:
              bin_dirname = os.path.basename(bin_dir) 
              if bin_dirname == 'bin' or bin_dirname == 'bin64': list_bin_dirs.append(bin_dir)
            if not list_bin_dirs: continue  # no bin/bin64 folders found
            # Now, collect the executables from these buried bin/bin64 folders
            for bin_dir in list_bin_dirs:
              exec_files = glob.glob(bin_dir + '/*')
              parse_exec_files(toolchain, module_name, vers_name, exec_files)
  


              print(' |-->> ', toolchain, module_name, vers_name, exec_name)




        # Counting found modules
        counter += 1
        print('{0}: finished with module: {1}'.format(counter, module_name))
        if counter > self.n_max_modules: break

    return litup

  #---------------------
  def write_list_executables(self, filename):
    """
    Write the self.list_executables as a space-delimitted ASCII file
    @param filename: the full path to the output filename
    @type filename: str
    """
    if not self.list_executables:
      logger.warning('write_list_executables: self.list_executables is empty. skipping ...')
      return

    lines = []
    for tup in self.list_executables:
      tc   = tup[0]
      mod  = tup[1]
      ver  = tup[2]
      ex   = tup[3]
      line = '{0} {1} {2} {3}\n'.format(tc, mod, ver, ex)
      lines.append(line)
    with open(filename, 'w') as w: w.writelines(lines)
    logger.info('write_list_executables: {0} saved'.format(filename))

  #---------------------
  def read_list_executables(self, filename):
    """

    """ 
    pass
  #---------------------
  def read_and_set_list_executables():
    """

    """
    pass
  
  #---------------------


  #---------------------
  # Executable Dictionary
  #---------------------
  def __set_dic_executables(self):
    """
    Set the self.executables attribute to the dictionary returned from calling the public
    method get_dic_executables()
    """
    if self.executables: return  # executables are already available; why bother?
    if self.executables_file is None: 
      message = '__set_dic_executables: self.executables_file is None.\n \
                       You may follow one of these approaches: \n \
                       + MyStat= stats.stats(exec_file="executables.txt") \n \
                         self.read_and_set_dic_executables("executables.txt") \n \
                       OR you may generate the executables_file, if it does not exist already \n \
                       + self.write_dic_executables("executables.txt") \n'
      logger.warning(message)
      print(message)
      raise RuntimeWarning
    else: 
      self.read_and_set_dic_executables(self.executables_file)

  #---------------------
  def get_dic_executables(self):
    """
    Walks through all modules in all toolchains, and searches for the "bin" or "bin64" folder under 
    all possible versions of that software. If the software/module has a "bin/bin64" folder, 
    then, the name of the executable is taken as the key, and name of the module is taken
    as the value of the dictionary. 
    E.g. the "R" package has a "bin" folder (for any of the toolchains and/or versions), and
    inside that, there are two executable files, called "R" and "Rscript". As a result, the
    self.executable dictionary would have two extra items (key/value) pairs as:
    self.executable = {..., 'R': 'R', 'Rscript': 'R', ...}. 

    Note: Two cases happen:
      + case a. The software has a bin/bin64 folder (or both), just right under the version folder
      + case b. The software might have a bin/bin64 (or both), but they are digged under folder 
                hierarchy, or there are multiple bin/bin64 folders available for a single version
    We treat both cases here.

    Note: calling this public method takes few minutes, so, one may write the outcome as an ASCII
          file and recycle that file later on. This ASCII file must be updated once in a while.
          For that, see the public method: write_dic_executables()

    Note: I discovered that there are some software with different module enames, but identical 
          executable names. Therefore, storing the unique keys results in overwriting the values.
          As a result of this, only the last module which has identical executable name is returned,
          and all former hits are lost. To avoid this, call get_list_executables() instead.

    @return: dictionary with keys the executable names, and values their corresponding module name
    @rtype: dict
    """
    # if self.executables is non-empty, just return its copy
    if self.executables:
      return self.executables.copy()
    else: 
      pass

    # Thus, below here, self.executables is empty
    dic = dict()

    #%%%%%%%%%%%%%%%%%%
    def print_this(ex, k, v):
      """ just define a local printing convenience function """
      print('{0}: {1}, {2}'.format(ex, k, v))
    #%%%%%%%%%%%%%%%%%%

    def add_key_val(key, val):
      """ add a key/val pair to self.executables if the key fulfils some requirements """
      flag_dat = '.dat' in key
      flag_txt = '.txt' in key
      flag_so  = '.so'  in key
      flag_conf= '.conf' in key or '.config' in key
      flag_cmd = '.cmd' in key
      flags    = [flag_dat, flag_txt, flag_so, flag_conf, flag_cmd]
      if not any(flags):
        dic[key] = val
    #%%%%%%%%%%%%%%%%%%

    # exclude modules that have no bin/bin64 folders in them
    exclude = set(['bin', 'accounting', 'intel_env', 'foss_env'])
    for toolchain in self.avail_toolchain:
      path = '/apps/leuven/{0}/{1}a/software'.format(self.cluster, toolchain)
      dirs = glob.glob(path + '/*')

      if len(dirs) == 0:
        logger.error('__set_dic_executables: Found no modules in {0}'.format(path))
        raise ValueError

      for mod in dirs:
        module_name = os.path.basename(mod)
        val         = module_name
        if module_name in exclude: continue
        module_vers = glob.glob(mod + '/*')

        for vers in module_vers:
          vers_name = os.path.basename(vers)
          bin_path  = '{0}/bin'.format(vers)
          bin64_path= '{0}/bin64'.format(vers)

          # Case a. The version folder already has bin/bin64 folder
          # executables in bin
          if os.path.exists(bin_path): 
            exec_files = glob.glob(bin_path + '/*')
            # key: exec filename, key: module name
            for exec_file in exec_files: 
              key = os.path.basename(exec_file)

              add_key_val(key, val)
#              print_this(exec_file, key, val)

          # executables in bin64
          elif os.path.exists(bin64_path):
            exec_files = glob.glob(bin64_path + '/*')
            # key: exec filename; key: module name
            for exec_file in exec_files:
              key = os.path.basename(exec_file)
 
              add_key_val(key, val)
#              print_this(exec_file, key, val)

          # Case b. the bin/bin64 folder is located few levels deeper in the directory tree!
          else: 
            # this finds the bin/bin64 folder, and all other junk; so, needs trimming later on
            maybe_bin_dirs = glob.glob(vers + '/**/bin*', recursive=True)
            if not maybe_bin_dirs: continue # has no bin/bin64 at all
            list_bin_dirs  = []
            for bin_dir in maybe_bin_dirs:
              bin_dirname = os.path.basename(bin_dir) 
              if bin_dirname == 'bin' or bin_dirname == 'bin64': list_bin_dirs.append(bin_dir)
            if not list_bin_dirs: continue  # no files inside the bin/bin64 folders
            # Now, collect the executables from the bin/bin64 folders
            for bin_dir in list_bin_dirs:
              exec_files = glob.glob(bin_dir + '/*')
              for exec_file in exec_files:
                key = os.path.basename(exec_file)

                add_key_val(key, val)
#                print_this(exec_file, key, val)

    return dic

  #---------------------
  def write_dic_executables(self, filename):
    """
    Write the executable list as an ASCII file
    @param filename: full path to the ASCII file to write to
    @type filename: str
    """
    if not self.executables: 
      logger.warning('write_dic_executables: self.executables is empty. Calling get_dic_executables()')
      self.__set_dic_executables()

    lines = []
    for key, val in self.executables.items(): lines.append('{0} {1}\n'.format(key, val))
    with open(filename, 'w') as w: w.writelines(lines)
    logger.info('write_dic_executables: stored {0}'.format(filename))

  #---------------------
  def read_dic_executables(self, filename):
    """
    Read the key/value item pairs of the executable list from the ASCII file, and return 
    the dictionary with the keys as the executable name (form the bin or bin64 directory) and the
    value is the module name
    Note: whether or not the self.executables dictionary is empty, we do NOT set the value of that
          attribute to the dictionary representation of the content of this ASCII file.

    @param filename: full path to the ASCII file to read from; the filenama is space-delimited
    @type filename: str
    @return: a dictionary, similar to what self.executables attribute must look like
    @rtype: dict
    """
    if not os.path.exists(filename):
      logger.warning('read_dic_executables: {0} does not exist'.format(filename))
      return None
    with open(filename, 'r') as r: lines = r.readlines()
    dic = dict()
    for line in lines:
      key, val = line.rstrip('\r\n').split()
      dic[key] = val
    
    return dic

  #---------------------
  def read_and_set_dic_executables(self, filename):
    """
    Read the executable list from the ASCII file and call the read_dic_executables() method. Then,
    set the self.executables attribute with the contents of this dictionary. This method is 
    complementory to the read_dic_executables() and __set_dic_executables()
    
    @param filename: full path to the ASCII file to read from; the filenama is space-delimited
    @type filename: str
    """
    if self.executables: 
      logger.warning('read_and_set_dic_executables: self.executables is non-empty. skipping ...')
      return None

    dic = self.read_dic_executables(filename)
    self.executables = dic.copy()

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
  def increment_module_count(self, which):
    """
    x
    """
    is_module = which in self.module_counter
    is_exec   = which in self.executables
#    is_found  = any([is_module, is_exec])

    if is_module: 
      module = which
    elif is_exec:
      # swapping the module name by providing the executable name, and get the module name
      module  = self.executables[which] 
    else: 
      logger.warning('increment_module_count: invalid key: {0}'.format(which))
      return
#      raise KeyError

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

##########################################################################

