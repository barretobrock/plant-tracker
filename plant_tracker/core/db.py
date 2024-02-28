from contextlib import contextmanager
import datetime
import pathlib
import re
from typing import (
    Any,
    List,
    Optional,
    Union
)

from pukr import PukrLog
from sqlalchemy.orm import Session

from plant_tracker.config import DevelopmentConfig, ProductionConfig
from plant_tracker.model import (
    Base,
    TableAlternateNames,
    TableMaintenanceLog,
    TableObservationLog,
    TablePlant,
    TablePlantFamily,
    TablePlantHabit,
    TablePlantImage,
    TablePlantRegion,
    TablePlantSubRegion,
    TableScheduledMaintenanceLog,
    TableScheduledWateringLog,
    TableSpecies,
    TableWateringLog
)


class DBAdmin:
    """For holding all the various ETL processes, delimited by table name or function of data stored"""
    TABLES = [
        TableAlternateNames,
        TableMaintenanceLog,
        TableObservationLog,
        TablePlant,
        TablePlantFamily,
        TablePlantHabit,
        TablePlantImage,
        TablePlantRegion,
        TablePlantSubRegion,
        TableScheduledMaintenanceLog,
        TableScheduledWateringLog,
        TableSpecies,
        TableWateringLog,
    ]

    def __init__(self, log: PukrLog, env: str = 'dev', tables: List = None):
        self.log = log

        self.log.debug('Obtaining credential file...')
        conf = ProductionConfig if env.upper() == 'PROD' else DevelopmentConfig
        conf.load_secrets()
        self.props = conf.SECRETS

        self.log.debug('Opening up the database...')
        conf.build_db_engine()
        self.session = conf.SESSION
        self.eng = conf.ENGINE

        self.tables = self.TABLES if tables is None else tables

    def drop_and_recreate(self):
        # Determine tables to drop
        self.log.debug(f'Dropping tables: {self.tables} from db...')
        tbl_objs = []
        for table in self.tables:
            tbl_objs.append(Base.metadata.tables.get(f'{table.__table_args__.get("schema")}.{table.__tablename__}'))
        Base.metadata.drop_all(self.eng, tables=tbl_objs)
        self.log.debug('Establishing database...')
        Base.metadata.create_all(self.eng)

    @contextmanager
    def session_mgr(self):
        session = self.session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def refresh_table_objects(self, tbl_objs: List, session: Session = None):
        new_objs = []
        for obj in tbl_objs:
            new_objs.append(self.refresh_table_object(tbl_obj=obj, session=session))
        return new_objs

    def refresh_table_object(self, tbl_obj, session: Session = None):
        """Refreshes a table object by adding it to the session, committing and refreshing it before
        removing it from the session"""

        def _refresh(sess: Session, tbl) -> Any:
            # Bind to session
            sess.add(tbl)
            # Prime, pull down changes
            sess.commit()
            # Populate changes to obj
            sess.refresh(tbl)
            # Remove obj from session
            sess.expunge(tbl)
            return tbl

        if session is None:
            with self.session_mgr() as session:
                tbl_obj = _refresh(sess=session, tbl=tbl_obj)
        else:
            # Working in an existing session
            tbl_obj = _refresh(sess=session, tbl=tbl_obj)
        return tbl_obj

    def get_family_by_id(self, family_id: int = None) -> Optional[TablePlantFamily]:
        if family_id is None:
            return family_id
        with self.session_mgr() as session:
            fam = session.query(TablePlantFamily).filter(TablePlantFamily.plant_family_id == family_id).one_or_none()
            if fam is not None:
                session.expunge(fam)
            return fam

    def get_habit_by_id(self, habit_id: int = None) -> Optional[TablePlantHabit]:
        if habit_id is None:
            return habit_id
        with self.session_mgr() as session:
            hab = session.query(TablePlantHabit).filter(TablePlantHabit.plant_habit_id == habit_id).one_or_none()
            if hab is not None:
                session.expunge(hab)
            return hab

    def get_species(self, common_name: str = None) -> Optional[TableSpecies]:
        with self.session_mgr() as session:
            s = session.query(TableSpecies).filter(TableSpecies.common_name == common_name).one_or_none()
            if s is not None:
                session.expunge(s)
            return s

    # def load_data(self):
    #     # Read in dim_plant
    #
    #
    #
    #
    #     # Load species
    #     for i, row in dim_plant_df.iterrows():
    #         self.log.debug(f'Working on item {i + 1}...')
    #         family_name_raw = self.clean_if_not_none(row, 'Family')
    #         family_name_obj = next((x for x in families if x.plant_family == family_name_raw), None)
    #         duration_raw = self.clean_if_not_none(row, 'Life Cycle')
    #         duration_obj = next((x for x in durations if x.plant_duration == duration_raw), None)
    #         habit_raw = self.clean_if_not_none(row, 'Growth Habit')
    #         habit_obj = next((x for x in habits if x.plant_habit == habit_raw), None)
    #
    #         pruning_tbl = None
    #         pruning_notes_raw = self.clean_if_not_none(row, 'Pruning Notes')
    #         if pruning_notes_raw is not None:
    #             self.log.debug('Adding pruning notes...')
    #             date_range = re.search(r'\d+-\d+ to \d+-\d+', pruning_notes_raw).group().split()
    #             info = re.sub(r'\d+-\d+ to \d+-\d+', '', pruning_notes_raw).strip()
    #             pruning_tbl = TableScheduledMaintenanceLog(
    #                 maintenance_type=pruning_type,
    #                 maintenance_period_start_mm=int(date_range[0].split('-')[0]),
    #                 maintenance_period_start_dd=int(date_range[0].split('-')[1]),
    #                 maintenance_period_end_mm=int(date_range[-1].split('-')[0]),
    #                 maintenance_period_end_dd=int(date_range[-1].split('-')[1]),
    #                 notes=info
    #             )
    #         # Get plants associated with species
    #         common_name = self.clean_if_not_none(row, 'Common Name')
    #         plants_raw = fact_plant_log_df.loc[fact_plant_log_df['name'] == common_name, :]
    #         plants = []
    #         for j, plant_row in plants_raw.iterrows():
    #             plant_source = self.clean_if_not_none(plant_row, 'source')
    #             plant_source_obj = next((x for x in sources if x.plant_source == plant_source), None)
    #             date_planted = self.clean_if_not_none(plant_row, 'date_planted')
    #             if date_planted is not None:
    #                 date_planted = datetime.datetime.strptime(date_planted, '%Y-%m-%d').date()
    #             plants.append(TablePlant(
    #                 plant_source=plant_source_obj,
    #                 date_planted=date_planted
    #             ))
    #
    #         species = TableSpecies(
    #             common_name=common_name,
    #             scientific_name=self.clean_if_not_none(row, 'Scientific Name'),
    #             plant_family=family_name_obj,
    #             duration=duration_obj,
    #             habit=habit_obj,
    #             is_native=self.clean_if_not_none(row, 'is_native'),
    #             leaf_retention_type=None,
    #             water_requirement=None,
    #             light_requirement=None,
    #             is_drought_tolerant=None,
    #             is_heat_tolerant=None,
    #             is_freeze_tolerant=None,
    #             usda_symbol=self.clean_if_not_none(row, 'USDA_symbol'),
    #             bloom_start_month=None,
    #             bloom_end_month=None,
    #             bloom_notes=None,
    #             care_notes=self.clean_if_not_none(row, 'Care Notes'),
    #             propagation_notes=None,
    #         )
    #
    #         with self.session_mgr() as session:
    #             species = self.refresh_table_object(species, session)
    #             if pruning_tbl is not None:
    #                 pruning_tbl.species = species
    #                 session.add(pruning_tbl)
    #             if len(plants) > 0:
    #                 for plant in plants:
    #                     plant.species = species
    #                     session.add(plant)
    #     with self.session_mgr() as session:
    #         species = session.query(TableSpecies).all()
    #         plants = session.query(TablePlant).all()


