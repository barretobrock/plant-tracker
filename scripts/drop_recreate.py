
from pukr import get_logger

from plant_tracker.core.db import DBAdmin

test_log = get_logger('drop_recreate', base_level='DEBUG')
db = DBAdmin(test_log, tables=DBAdmin.TABLES)

db.drop_and_recreate()
