"""
Author: Ehsan Moravveji
Date:   10 Jan 2018
Purpose: This test suite will check different features of the package during the development phase.
        There are basically no valid exit/exception values returned.
"""

import sys, os, glob
import logging
import time
import xml.etree.ElementTree as ET
from numpy.random import shuffle

from module_stat import job_xml, scripts, stats

###########################################################
logger = logging.getLogger(__name__)
logging.basicConfig(filename='module-stat.log',level=logging.INFO)
###########################################################

###########################################################
def test_module_stat():

  # Choose target repository of scripts
#  repos_scripts = '/apps/leuven/icts/jobscripts/2017-10-12'
  repos_scripts = '/apps/leuven/icts/jobscripts'
  script_files  = glob.glob(repos_scripts+'/**/*.SC', recursive=True)
  shuffle(script_files)

  # Collect statistics for this folder
  stat = stats.stats()

  # Count module loads
  n_all, n_OK, n_bad = 0, 0, 0
  for script_file in script_files:
    n_all += 1
    try:
      scr = scripts.script(script_file)
    except Exception as err:
      continue
    if isinstance(scr, type(None)): raise TypeError
#    print(scr.file_sc, scr.toolchain, scr.loaded)
    if not scr.loaded: continue
    for key in scr.loaded.keys():
      try:
        stat.increment_module_count(key)
      except KeyError:
        continue

    n_OK += 1     
  n_bad = n_all - n_OK
  p_OK  = n_OK / n_all * 1e2
  print('All: {0}; OK: {1}; Bad: {2} => percent OK: {3:.2f}%'.format(n_all, n_OK, n_bad, p_OK))

  showtop = 50
  top_mod, top_count = stat.sort_module_counts(showtop)
#  for mod, cnt in zip(top_mod, top_count):
#    print(mod, cnt)
  stat.write_sort_module_counts_as_ascii(showtop)

#  for module, count in stat.module_counter.items():
#    if count > 0: print(module, count)

###########################################################
def test_single_script():
  start         = time.time()
  repos_scripts = '/apps/leuven/icts/jobscripts/2017-10-12'
  script_files  = glob.glob(repos_scripts+'/**/*.SC', recursive=True)
  t_glob        = time.time() 
  n_scr         = len(script_files)
  logger.info('test_single_scripts: Found "{0}" .SC script files, in {1:.1f} sec'.format(n_scr, t_glob-start))
  print('test_single_scripts: Found "{0}" .SC script files, in {1:.2f} sec'.format(n_scr, t_glob-start))
  
  shuffle(script_files)
  n_OK, n_pass  = 0, 0
  for i, script_file in enumerate(script_files[:1000]):
    try:
      with scripts.script(script_file) as scr:
        n_OK    += 1
    except:
      n_pass    += 1
      pass

  t_loop        = time.time()
  print('test_single_scripts: n_OK={0}, n_pass={1}, dt={2:.1f} sec'.format(n_OK, n_pass, t_loop-t_glob))

 
###########################################################
def test_module_scripts2():

  with stats.stats() as stat:
    av_mod = stat.get_avail_modules(2016)
    mcnt = stat.module_counter
  for key in mcnt.keys():
    if isinstance(key, str): 
      print(key)
    else:
      print('None detected')

  print('How many independent modules are there? ' + str(len(mcnt)) )
  
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
    stat = test_module_scripts2()
    if stat != 0: sys.exit(stat) 

  if False:
    stat = test_single_script()
    if stat != 0: sys.exit(stat) 

  if True:
    stat = test_module_stat()
    if stat != 0: sys.exit(stat)
  
###########################################################
