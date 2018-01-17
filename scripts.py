"""
Author: Ehsan Moravveji
Date: 09 January 2018
Purpose: This module manipulates the PBS job scripts by combining the job_xml.JB class 
         with the modules.module class in order to combine the content of the PBS script
         preamble (i.e. PBS directives), and the body of the script (which contains specification
         of the toolchain and the modules to load.
"""
import sys, os, glob
import logging

from .job_xml import JB
from .modules import module

##########################################################################
logger = logging.getLogger(__name__)
##########################################################################
 
class script(JB, module):
  """
  This class extends the functionality of the two parent classes JB and module.
  Tip: wrap the instantiation through a try/except block to capture the FileNotFoundError.
  """
  #---------------------
  def __init__(self, file_sc):
    """
    Constructor
    
    @param file_sc: the full path to the script file
    @type file_sc: str
    """
    if not os.path.exists(file_sc):
      logger.error('__init__: "{0}" does not exist.'.format(file_sc))
      raise FileNotFoundError

    file_xml      = get_xml_filename(file_sc)
    if file_xml is False or not os.path.exists(file_xml):
      logger.warning('__init__: the companion .JB XML file not found.')
      raise FileNotFoundError

    self.file_sc  = file_sc  # Original script with extension .SC
    self.file_xml = file_xml # The XML .JB file

    # Initialize the two parent classes
    JB.__init__(self, self.file_xml)
    module.__init__(self, self.file_sc)

  #---------------------
  def __enter__(self):
    return self

  #---------------------
  def __exit__(self, type, value, traceback):
    if isinstance(self, type(None)):
      logger.warning('__exit__: self cannot be None.')
      raise TypeError

  #---------------------

##########################################################################
def get_xml_filename(file_sc):
  """
  Convert the script file to the XML filename by substituting the .SC extension
  in the former with the .JB for the latter

  @param file_sc: the name of the original script file
  @type file_sc: str
  @return: replace the extension (.SC --> .JB), and return the new full path.
           it is expected that the .JB file is sitting alongside the .SC file,
           else something is going wrong.
  @rtype: str
  """
  if file_sc[-3:] != '.SC':
    logger.warning('get_xml_filename: Wrong script file (bad extension) is provided.') 
    return False

  return file_sc.replace('.SC', '.JB')

##########################################################################


