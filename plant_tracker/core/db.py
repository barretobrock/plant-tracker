from contextlib import contextmanager
from typing import (
    List,
    Optional
)

from pukr import PukrLog
from sqlalchemy.orm import Session

from plant_tracker.config import DevelopmentConfig, ProductionConfig
from plant_tracker.model import (
    Base,
    TableAlternateNames,
    TableGeodata,
    TableImage,
    TableMaintenanceLog,
    TableObservationLog,
    TablePlant,
    TablePlantFamily,
    TablePlantHabit,
    TablePlantLocation,
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
        TableGeodata,
        TableImage,
        TableMaintenanceLog,
        TableObservationLog,
        TablePlant,
        TablePlantFamily,
        TablePlantHabit,
        TablePlantLocation,
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
        if session is None:
            with self.session_mgr() as session:
                for obj in tbl_objs:
                    new_objs.append(self.refresh_table_object(tbl_obj=obj, session=session))
        else:
            for obj in tbl_objs:
                new_objs.append(self.refresh_table_object(tbl_obj=obj, session=session))
        return new_objs

    @staticmethod
    def commit_and_refresh_table_obj(session, table_obj, do_expunge: bool = False):
        # Bind to session
        session.add(table_obj)
        # Prime, pull down changes
        session.commit()
        # Populate changes to obj
        session.refresh(table_obj)
        if do_expunge:
            # Remove obj from session
            session.expunge(table_obj)
        return table_obj

    def refresh_table_object(self, tbl_obj, session: Session = None):
        """Refreshes a table object by adding it to the session, committing and refreshing it before
        removing it from the session"""

        if session is None:
            with self.session_mgr() as session:
                tbl_obj = self.commit_and_refresh_table_obj(session=session, table_obj=tbl_obj, do_expunge=True)
        else:
            # Working in an existing session
            tbl_obj = self.commit_and_refresh_table_obj(session=session, table_obj=tbl_obj, do_expunge=True)
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
