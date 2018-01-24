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
if __name__ == '__main__':

  if False:
    stat = count_independent_modules()
    if stat != 0: sys.exit(stat) 

  if False:
    stat = count_good_bad_scripts()

  if False:
    stat = collect_module_use_stats()
    if stat != 0: sys.exit(stat)
  
###########################################################
