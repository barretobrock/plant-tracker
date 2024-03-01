
from pukr import get_logger

from plant_tracker.core.etl import ETL

test_log = get_logger('load_data', base_level='DEBUG')
etl = ETL(test_log)

etl.load_attr_tables()
etl.load_families()
etl.load_species()
etl.load_plants()

