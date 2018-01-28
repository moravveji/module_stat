"""
Author: Ehsan Moravveji
Date:   09 January 2018
Purpose: This module defines a class to manipulte the MOAB XML files
"""

import sys, os, glob
import logging
import xml.etree.ElementTree as ET

##########################################################################
logger = logging.getLogger(__name__)
##########################################################################

class JB:
  """
  The class which manipulates the XML files. 
  Tip: wrap the instantiation through a try/except block to capture the FileNotFoundError.
  """
  #---------------------
  def __init__(self, file_xml):
    """
    Constructor
    The names of the (most) attributes match the tags of the XML .pbs script files.

    @param file_xml: full path to the XML file to be manipulated
    @type file_xml: str  
    """
    if not os.path.exists(file_xml):
      logger.error('__init__: "{0}" does not exist.'.format(file_xml))
      raise FileNotFoundError
    # XML filename is the only mandatory attribute of the class
    self.file_xml = file_xml
    
    # XML root element
    self.root = self.getroot()

    # Exclude these attributes from automatic searching for the relevant XML element
    self.exclude = ['file_xml', 'root', 'exclude', 'ppn']

    # XML attributes
    self.jobid = None          # e.g. 20704400.moab.tier2.leuven.vsc
    self.queue = None          # e.g. q1h, q24h, etc
    self.Job_Name = None       # specified by #PBS -N 
    self.job_state = None      # e.g. C for completed
    self.Account_Name = None   # specifid by #PBS -A
    self.ctime = None          # ?
    self.mtime = None          # ?
    self.qtime = None          # ?
    self.etime = None          # ?
    self.Priority = None       # ?
    self.nodes = None          # specified by #PBS -l nodes:ppn
    self.nodect = None         # specified by #PBS -l nodes
    self.pmem = None           # specified by #PBS -l pmem
    self.walltime = None       # specified by #PBS -l walltime
    self.euser = None          # vsc number
    self.egroup = None         # effective user group name
    self.submit_arg = None     # ? worker? other kind of jobs?
    self.comp_time = None      # ? effective cpu time for all nodes? 
    self.total_runtime = None  # ? nodes x comp_time? 

    # Other attributes
    self.ppn = 1               # specified by #PBS -l ppn; defaults to 1 core
    self.machine = None        # specified by #PBS -l, is either 'ivybridge' or 'haswell'

    # Apply methods:
    # Allocate the values of the tags from the relevant dictionary of the key/value pairs
    self.__allocate()
    self.__set_ppn()

  #---------------------
  def __enter__(self):
    return self

  #---------------------
  def __exit__(self, type, value, traceback):
    pass

  #---------------------
  def __allocate(self):
    """
    Reads the XML file and fills up the attributes of the class with the
    relevant tag-value pairs from the XML file. 
    """
    d = self.as_dict()
    for key, val in d.items():
      setattr(self, key, val)

  #---------------------
  def as_dict(self):
    """
    Returns all element tag/text pairs as a dictionary key/value pairs.
    With this, the repeated tag/text pairs (if the tags repeat) are replaced
    with their last value. Also note that the XML hierarchy is totally violated
    and the returned key/value pairs obey no order (as expected from dictionaries).
    
    @return: dictionary object whose keys are the XML tags and whose values are the
             corresponding text.
    @rtype: dict
    """
    d = dict()
    attrs = set([a for a in self.__dict__.keys() if not (a.startswith('__') and a.endswith('__')) ])
    for throw in self.exclude: attrs.remove(throw)
    
    for elem in self.root.iter():
      if elem.tag not in attrs: continue
      d[elem.tag] = elem.text
    
    return d      

  #---------------------
  def getroot(self):
    """
    Return the root element of the XML file. Therefore, the reading of the entire XML
    file is carried once here. Since we iterate later over the root elements (the root.iter()
    method), only the root element sufficies for all our application
    @return: an instance of xml.etree.ElementTree.Element class
    @rtype: class
    """
    fname = self.file_xml
    handle = ET.parse(fname)

    return handle.getroot()

  #---------------------
  def __set_ppn(self):
     """
     Retrieve the value of the ppn (processes/cores per node) from 
     """
     nodes = self.nodes
     if nodes is None: return
     if ':' not in nodes: return

     #.............................
     def get_ppn_and_machine(parts):
       """ Specification of ppn, nodes and machine has no ordering, do handle it decently """
       ppn, machine = 1, None # defaults
       for p in parts:
         if p == 'haswell': machine = 'haswell'
         if p == 'ivybrdige': machine = 'ivybridge'
         if 'ppn' in p: ppn = int(p[4:])

       return ppn, machine
     #.............................
  
     parts = nodes.split(':')
     n_parts = len(parts)
     if n_parts == 1:
       logger.error('__set_ppn: nodes={0}'.format(nodes))
       ppn = 1
       machine = None
     elif n_parts == 2 or n_parts == 3:
       ppn, machine = get_ppn_and_machine(parts)
     else:
       logger.error('__set_ppn: Expecting nodes to have only max 3 pieces; but has len={0}'.format(n_parts))
       raise IndexError 

     self.ppn = ppn
     self.machine = machine

  #---------------------
  #---------------------





