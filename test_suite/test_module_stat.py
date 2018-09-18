"""
Author: Ehsan Moravveji
Date:   10 Jan 2018
Purpose: This test suite will check different features of the package during the development phase.
        There are basically no valid exit/exception values returned.
"""

import sys, os, glob
import logging
import xml.etree.ElementTree as ET

from module_stat import job_xml, scripts, stats

###########################################################
logger = logging.getLogger(__name__)
logging.basicConfig(filename='module-stat.log',level=logging.INFO)
###########################################################

###########################################################
###########################################################
def test_get_list_executables():
  """
  test get_list_executables() method
  """
  with stats.stats(cluster='ThinKing', auto=False) as stat:
    list_exec = stat.get_list_executables()
    n_exec    = len(list_exec)
    logger.info('We found {0} distinct executables'.format(n_exec))
    print('We found {0} distinct executables'.format(n_exec))
    print(list_exec)

###########################################################
def test_module_stat_used_one():
  """ test self.used only for one script """
  stat     = stats.stats(exec_file="executables.txt")
  path_jobscript  = '/apps/leuven/icts/jobscripts'
  date_dir        = '2017-09-15'
  sample_script   = '20602304.moab.tier2.leuven.vsc.SC' # <-- OK
  path_script     = '/'.join([path_jobscript, date_dir, sample_script])
  scr             = scripts.script(path_script)
  print(scr.loaded)
  print(scr.called)
  print(scr.used)
  for key in scr.used.keys():
    try:
      stat.increment_module_count(key)
    except KeyError:
      continue
  for key, val in stat.module_counter.items():
    if val > 0:
      print(key, val)
  
###########################################################
def test_module_stat_executables():

  stat     = stats.stats(exec_file="executables.txt")
  #stat.write_dic_executables('executables.txt')
  stat.read_and_set_dic_executables('executables.txt')
  dic_exec = stat.get_dic_executables()
  print('mcc: ', dic_exec['mcc'])
#  print('g09: ', dic_exec['g09'])
  
###########################################################
def test_module_scripts():

  path_jobscript  = '/apps/leuven/icts/jobscripts'
  sample_script   = '20704400.moab.tier2.leuven.vsc.SC' # <-- no .SC file!
#  sample_script   = '20713982.moab.tier2.leuven.vsc.SC' # <-- OK
  sample_script   = '2017-10-12/20614337.moab.tier2.leuven.vsc.SC' # <-- detect toolchain?
  path_script     = '/'.join([path_jobscript, sample_script])

  # check the try/except block
  try:
    with scripts.script(path_script) as scr:
      print('try: success')
  except:
    logger.error('test_module_scripts: exception raised. exiting gracefully')
    pass

  # direct with-statement
  with scripts.script(path_script) as scr: 
    print(type(scr))
    print('queue: ' + scr.queue)
    print('toolchain: {0}'.format(scr.toolchain))
    print('modules: ', scr.loaded)

  return 0
  
###########################################################
def test_module_job_xml():

  path_jobscripts = '/apps/leuven/icts/jobscripts'
  sample_xml = '20704400.moab.tier2.leuven.vsc.JB'
  path_xml   = '/'.join([path_jobscripts, sample_xml])
  if not os.path.exists(path_xml):
    logger.error('test_module_job_xml: XML file: "{0}" does not exist'.format(path_xml))
    return False

  # direct instantiation
  this = job_xml.JB(path_xml)
  dic  = this.as_dict()
 
  # instantiating with the "with" block
  with job_xml.JB(path_xml) as that: print(that.queue)

  return 0

###########################################################
def test_a_xml_file():

  path_jobscripts = '/apps/leuven/icts/jobscripts'
  sample_xml = '20704400.moab.tier2.leuven.vsc.JB'
  path_xml   = '/'.join([path_jobscripts, sample_xml])
  if not os.path.exists(path_xml):
    logger.error('test_a_xml_file: XML file: "{0}" does not exist'.format(path_xml))
    return False
  xml  = ET.parse(path_xml)
  root = xml.getroot()
#  print('root.tag: ', root.tag, dir(root))

  elem_queue = root.find('queue')
  print(':'.join([elem_queue.tag, elem_queue.text]))

  d = dict()
  for elem in root.iter(): 
    d[elem.tag] = elem.text
  print(d)

  elem_account = root.findall('Account_Name')

#  for child in root: 
#    print(child.tag, child.text)

  print()

  attributes = root[-1]
#  for subattr in attributes:
#    print('{0}: {1}'.format(subattr.tag, subattr.text))

  return 0
  
###########################################################
if __name__ == '__main__':
  if False: 
    stat = test_a_xml_file()
    if stat != 0: sys.exit(stat)

  if False:
    stat = test_module_job_xml()
    if stat != 0: sys.exit(stat)

  if False:
    stat = test_module_scripts()
    if stat != 0: sys.exit(stat) 

  if False:
    stat = test_module_stat_executables()
    if stat != 0: sys.exit(stat)

  if False:
    stat = test_module_stat_used_one()
    if stat != 0: sys.exit(stat)

  if True:
    stat = test_get_list_executables()
    if stat != 0: sys.exit(stat)
  
###########################################################
