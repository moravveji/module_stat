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
logging.basicConfig(filename='run-module-stat.log',level=logging.INFO)
###########################################################

###########################################################
def collect_module_use_stats():

  # Choose target repository of scripts
#  repos_scripts = '/apps/leuven/icts/jobscripts/2017-10-21' # 1 day
#  repos_scripts = '/apps/leuven/icts/jobscripts/2017-10-2*' # 10 days
  repos_scripts = '/apps/leuven/icts/jobscripts' # all jobs
  script_files  = glob.glob(repos_scripts+'/**/*.SC', recursive=True)
  shuffle(script_files)

  # Collect statistics for this folder
  stat = stats.stats('executables.txt')

  # Count module loads
  n_all, n_OK, n_no_JB, n_no_use, n_None = 0, 0, 0, 0, 0
  for script_file in script_files:
    n_all += 1
    try:
      scr = scripts.script(script_file)
    except Exception as err:
      logger.error(repr(err) + ': ' + script_file)
      n_no_JB += 1
      continue
    if isinstance(scr, type(None)): 
      print(None, script_file)
      n_None += 1
      raise TypeError
    if not scr.used: 
      logger.warning('no use: ' + script_file)
      n_no_use += 1
      continue
    for key in scr.used.keys():
      try:
        stat.increment_module_count(key)
      except KeyError:
        continue

    n_OK += 1     
  p_OK  = n_OK / n_all * 1e2
  p_no_JB = n_no_JB / n_all * 1e2
  print('All: {0}; OK: {1}; no_use: {2}, no_JB: {3}, None: {4}'.format(
         n_all, n_OK, n_no_use, n_no_JB, n_None))
  print(' => percent OK: {0:.2f}%, no_JB: {1:.2f}%'.format(p_OK, p_no_JB))

  showtop = 50
  top_mod, top_count = stat.sort_module_counts(showtop)
#  for mod, cnt in zip(top_mod, top_count):
#    print(mod, cnt)
  stat.write_sort_module_counts_as_ascii(showtop)

#  for module, count in stat.module_counter.items():
#    if count > 0: print(module, count)

###########################################################
def count_good_bad_scripts():
  start         = time.time()
  repos_scripts = '/apps/leuven/icts/jobscripts/2017-10-12'
  script_files  = glob.glob(repos_scripts+'/**/*.SC', recursive=True)
  t_glob        = time.time() 
  n_scr         = len(script_files)
  logger.info('count_good_bad_scripts: Found "{0}" .SC script files, in {1:.1f} sec'.format(n_scr, t_glob-start))
  print('count_good_bad_scripts: Found "{0}" .SC script files, in {1:.2f} sec'.format(n_scr, t_glob-start))
  
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
  print('count_good_bad_scripts: n_OK={0}, n_pass={1}, dt={2:.1f} sec'.format(n_OK, n_pass, t_loop-t_glob))

###########################################################
def count_scripts_without_module_load():
  """
  What percentage of the scripts do not load any modules in the?
  """
  repos_scripts = '/apps/leuven/icts/jobscripts/2017-10-10'
  script_files  = glob.glob(repos_scripts + '/**/*.SC', recursive=True)
  n_scr         = len(script_files)

  n_OK, n_fail = 0, 0 # for jobs that failed
  n_has, n_does_not = 0, 0 # for modules that have even a single "module load ..." 
  for i, script_file in enumerate(script_files):
    try:
      with scripts.script(script_file) as scr:
        if scr.loaded:
          n_has += 1
        else:
          n_does_not += 1
        n_OK += 1
    except:  # FileNotFoundError or etc.
      pass
#      n_fail += 1

  n_mod = n_has + n_does_not
  p_has = n_has / n_mod * 1e2
  p_does_not = n_does_not / n_mod * 1e2

  n_tot = n_scr
  n_fail= n_tot - n_OK
  p_OK  = n_OK / n_tot * 1e2
  p_fail= n_fail / n_tot * 1e2

  print('\nn_scr={0}'.format(n_scr))
  print('n_OK:{0}, n_fail:{1}'.format(n_OK, n_fail))
  print('n_has:{0}, n_does_not:{1}'.format(n_has, n_does_not))

  print('\n"{0}" scripts have module loads and "{1}" do not load modules'.format(n_has, n_does_not))
  print('"{0:.2f}%" have module loads, and "{1:.2f}%" do not load modules'.format(p_has, p_does_not))
  print('"{0:.2f}%" of jobs succeeded, out of "{1}" jobs'.format(p_OK, n_tot))

  try: 
    assert n_OK == n_has + n_does_not
    print('Assert: numbers match as expected\n')
    return -1
  except AssertionError:
    print('AssertionError: numbers do not match: n_tot != n_has + n_does_not\n')
    return 0

###########################################################
def count_independent_modules():

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
def write_module_executables():

  stat     = stats.stats()
  stat.write_dic_executables('executables.txt')

  return 0
  
###########################################################
if __name__ == '__main__':

  if False:
    stat = count_independent_modules()
    if stat != 0: sys.exit(stat) 

  if False:
    stat = count_good_bad_scripts()

  if False:
    stat = collect_module_use_stats()
    if stat != 0: sys.exit(stat)

  if True:
    stat = count_scripts_without_module_load()
    if stat != 0: sys.exit(stat)

  if False:
    stat = write_module_executables()
    if stat != 0: sys.exit(stat)
  
###########################################################
