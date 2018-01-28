"""
Author: Ehsan Moravveji
Date:   28 January 2018
Purpose: This script tests the functionalities of the module "database.py"
"""

import sys, os, glob
import logging
from module_stat import database as mdb

###########################################################
logger = logging.getLogger(__name__)
logging.basicConfig(filename='test-database.log',level=logging.INFO)
###########################################################



###########################################################
def t03_execute_sql_script(name, scriptfile):
  print('\n Test executing a SQL script')
  try:
    db = mdb.database(name)
    db.execute_sql_script(scriptfile)
    logger.info('T03: success')
    return 0
  except Exception as err:
    logger.error('T03: Failed; error={0}'.format(err))
    return 1

###########################################################
def t01_create_simple_db(name):
  print('\n Test creating a simple database')
  try:
    db = mdb.database(name)
    db.conn.execute('create table family (name text, role text)')
    Family = [('John', 'parent'), ('Sara', 'parent'), ('Peter', 'child'), ('Ana', 'child')]
    db.conn.executemany('insert into family(name, role) values (?, ?)', Family)
    for member in db.conn.execute('select name, role from family'):
      print(member)
    logger.info('T01: success')
    return 0

  except Exception as err:
    logger.error('T01: error={0}'.format(err))
    return 1

###########################################################
def t02_create_delete_db(name):
  print('\n Test creating and deleting a database')
  try:
    db = mdb.database(name) 
    db.drop()
    return 0
  except Exception as err:
    logger.error('T02: error={0}'.format(err))
    return 1

###########################################################
if __name__ == '__main__':

  which_db = 'delete_me.db'
  which_script = 'example.sql'

  if True:
    sys.exit( t03_execute_sql_script(which_db, which_script) )

  if False:
    sys.exit( t01_create_simple_db(which_db) )

  if True:
    sys.exit( t02_create_delete_db(which_db) )

###########################################################


