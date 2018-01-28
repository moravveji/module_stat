# Statistics of the Used Modules on KULeuven VSC

## About
This python package counts the number of times different available modules are loaded in all PBS job scripts which are submitted to the MOAB scheduler. Different modules define different classes, which contain data and methods to contain the resource requirements/used of a job (in `job_xml.py` file), and the module toolchain and loads (in `modules.py` file). Then, a child class is built (in `scripts.py` file) that is used to process each script. A basic use of the package is the following (though you may combine much more intricate attributes of the `scripts.script` class).

## Basic Use
The following example block shows how to enumerate the number of module loads in a repository of job scripts, and to write down the ranking list to an ASCII file. The purpose of this example is to show the preferred use of `with` statements, and the `try` and `except` blocks. 

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

## Module Contents
The following modules are defined in this package:
+ `job_xml` provides the `JB` class to read and manipulate the .JB XML files created by MOAB for those jobs that are successfully scheduled by the scheduler.
+ `modules` provides the `module` class to manipulate the .SC PBD job scripts, and to extract the toolchain year and the whole list of loaded modules from that file. There is a difficulty to consistently collect loaded modules with a correct toolchain in some job scripts, for the following two reasons:
  1. some users hard-code their choice of toolchain in their `.bashrc` or their `.bash_profile` files, which for now I do not touch. For this reason, I loose track of the correct toolchain year, and I take the default as 2014.
  2. some users swap between different toolchain years more than once, and juggle with the `module load` and `module purge` repeatedly. This also complicates the statistics of specific version of a software too difficult.
+ `scripts` provides a child class `script` from the two `JB` and `module` classes, and takes care of the manipulation of the .SC and .JB files under the hood.
+ `stats` provides the `stat` class to count the number of times any module is loaded
+ `database` (**private**) stores the useful information of the installed software to a database 
+ `test_module_stat` is a basic test suite for different functionalities and modules
+ `test_database` checks different units and methods of the `database` module/class
+ `run_module_stat` provides few runtime examples for using this package

## Notes
+ As the development evolved, I noticed that a better data structure could have been used for some attributes of some of the classes. E.g. `stats.loaded`, `stats.called` and `stats.used` are currently dictionaries where in most cases the values of the keys are `None`; for these attributes, the use of Python `set` could have done the job similarly, with an added benefit of using somehow less RAM. The only point here is that the abovementioned dictionaries do not grow too large per each script, so, it is pretty safe to live with the current development.

## Dependencies
+ Python 3.6
+ numpy
+ xml.etree.ElementTree

