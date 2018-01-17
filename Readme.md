# Statistics of the Used Modules on KULeuven VSC

[TOC]

## About
This python package counts the number of times different available modules are loaded in all PBS job scripts which are submitted to the MOAB scheduler. Different modules define different classes, which contain data and methods to contain the resource requirements/used of a job (in `job_xml.py` file), and the module toolchain and loads (in `modules.py` file). Then, a child class is built (in `scripts.py` file) that is used to process each script. A basic use of the package is the following (though you may combine much more intricate attributes of the `scripts.script` class).

## Basic Use
The following example block shows how to enumerate the number of module loads in a repository of job scripts, and to write down the ranking list to an ASCII file. The purpose of this example is to show the preferred use of `with` statements, and the `try/except` blocks. 

```python
import sys, os, glob
import logging
from module_stat import scripts, stats

###########################################################
logger = logging.getLogger(__name__)
logging.basicConfig(filename='module-stat.log',level=logging.INFO)
###########################################################

###########################################################
def test_module_stat():

  # Choose target repository of scripts
  repos_scripts = '<path/to/jobscript/repository>' 
  script_files  = glob.glob(repos_scripts+'/**/*.SC', recursive=True)

  # Collect statistics for this folder
  stat = stats.stats()

  # Count module loads, and enumerate successful jobs
  n_all, n_OK, n_bad = 0, 0, 0
  for script_file in script_files:
    n_all += 1
    try:
      scr = scripts.script(script_file)
    except Exception as err:
      continue
    if isinstance(scr, type(None)): raise TypeError
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
  for mod, cnt in zip(top_mod, top_count): print(mod, cnt)
  stat.write_sort_module_counts_as_ascii(showtop)

if __name__ == '__main__':
  status = test_module_stat()
  sys.exit(status)
```

## Content

