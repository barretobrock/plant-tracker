import datetime
import pathlib
import re
from typing import (
    Dict,
    List,
    Optional,
    Union
)

from loguru import logger
import pandas as pd


from plant_tracker.model import (
    Base,
    DurationType,
    LeafRetentionType,
    LightRequirementType,
    MaintenanceType,
    ObservationType,
    PlantSourceType,
    TableMaintenanceLog,
    TableObservationLog,
    TablePlant,
    TablePlantFamily,
    TablePlantHabit,
    TablePlantRegion,
    TablePlantSubRegion,
    TableScheduledMaintenanceLog,
    TableScheduledWateringLog,
    TableSpecies,
    TableWateringLog,
    WaterRequirementType
)
from .db import DBAdmin


class ETL(DBAdmin):

    def __init__(self, log):
        self.root_dir = pathlib.Path(__file__).parent.parent.parent
        super().__init__(log=log, tables=self.TABLES)

        dim_plant_path = self.root_dir.joinpath('dim_plant.csv')
        dim_plant_df = pd.read_csv(dim_plant_path, sep=',', skiprows=[0])
        self.dim_plant_df = dim_plant_df.loc[~dim_plant_df['Common Name'].isna(), :]

        fact_plant_log_path = self.root_dir.joinpath('fact_plant_log.csv')
        fact_plant_log_df = pd.read_csv(fact_plant_log_path, sep=',')
        self.fact_plant_log_df = fact_plant_log_df.loc[~fact_plant_log_df['name'].isna(), :]

    @classmethod
    def clean_if_not_none(cls, series: pd.Series, source_val: str) -> Optional[Union[str, int]]:
        val = series[source_val]
        if val is None or pd.isna(val):
            return None

        if isinstance(val, str):
            return val.strip()
        return val

    def load_attr_tables(self):
        def get_uniques(col_name: str) -> List[str]:
            return self.dim_plant_df[col_name].dropna().unique().tolist()

        attr_tables = {
            TablePlantFamily: [TablePlantFamily(scientific_name=x) for x in get_uniques('Family')],
            TablePlantHabit: [TablePlantHabit(x) for x in get_uniques('Growth Habit')],
        }

        for tbl_obj, table_list in attr_tables.items():
            # Get pre-exising attrs
            with self.session_mgr() as session:
                items = session.query(tbl_obj).all()
                if len(items) == 0:
                    # add items
                    self.log.debug(f'Adding {len(table_list)} items to {tbl_obj.__name__}')
                    session.add_all(table_list)
                else:
                    self.log.debug(f'Bypassing {tbl_obj.__name__}')

    def load_species(self):
        with self.session_mgr() as session:
            families = [(x.plant_family_id, x.scientific_name) for x in session.query(TablePlantFamily).all()]
            habits = [(x.plant_habit_id, x.plant_habit) for x in session.query(TablePlantHabit).all()]

        for i, row in self.dim_plant_df.iterrows():
            common_name = self.clean_if_not_none(row, 'Common Name')
            self.log.debug(f'Working on {common_name}...')
            family_id = duration = habit_id = None
            family_name_raw = self.clean_if_not_none(row, 'Family')
            if family_name_raw is not None:
                family_id = next((x[0] for x in families if x[1] == family_name_raw), None)
            duration_raw = self.clean_if_not_none(row, 'Life Cycle')
            if duration_raw is not None:
                duration = DurationType[duration_raw.upper()]
            habit_raw = self.clean_if_not_none(row, 'Growth Habit')
            if habit_raw is not None:
                habit_id = next((x[0] for x in habits if x[1] == habit_raw), None)

            pruning_notes_raw = self.clean_if_not_none(row, 'Pruning Notes')
            pruning_tbl = None
            if pruning_notes_raw is not None:
                self.log.debug('Adding pruning notes...')
                date_range = re.search(r'\d+-\d+ to \d+-\d+', pruning_notes_raw).group().split()
                info = re.sub(r'\d+-\d+ to \d+-\d+', '', pruning_notes_raw).strip()
                pruning_tbl = TableScheduledMaintenanceLog(
                    maintenance_type=MaintenanceType.PRUNE,
                    maintenance_period_start_mm=int(date_range[0].split('-')[0]),
                    maintenance_period_start_dd=int(date_range[0].split('-')[1]),
                    maintenance_period_end_mm=int(date_range[-1].split('-')[0]),
                    maintenance_period_end_dd=int(date_range[-1].split('-')[1]),
                    notes=info
                )
            with self.session_mgr() as session:
                pt_list = []
                if pruning_tbl is not None:
                    pt_list.append(pruning_tbl)
                    session.add(pruning_tbl)
                genus = sp = None
                sci_name = self.clean_if_not_none(row, 'Scientific Name')
                if sci_name:
                    sci_name_split = sci_name.split(' ', maxsplit=1)
                    genus = sci_name_split[0]
                    sp = sci_name_split[1]
                species = TableSpecies(
                    common_name=common_name,
                    genus=genus,
                    species=sp,
                    scientific_name=sci_name,
                    plant_family=self.get_family_by_id(family_id),
                    duration=duration,
                    habit=self.get_habit_by_id(habit_id),
                    is_native=self.clean_if_not_none(row, 'is_native'),
                    leaf_retention=None,
                    water_requirement=None,
                    light_requirement=None,
                    is_drought_tolerant=None,
                    is_heat_tolerant=None,
                    is_freeze_tolerant=None,
                    usda_symbol=self.clean_if_not_none(row, 'USDA_symbol'),
                    bloom_start_month=None,
                    bloom_end_month=None,
                    bloom_notes=None,
                    care_notes=self.clean_if_not_none(row, 'Care Notes'),
                    propagation_notes=None,
                    scheduled_maintenance_logs=pt_list
                )
                session.add(species)
                session.commit()
            self.log.debug(f'Added to db.')

    def load_plants(self):
        self.log.info('Working on individual plants...')
        for i, row in self.fact_plant_log_df.iterrows():
            common_name = self.clean_if_not_none(row, 'name')
            date_planted = self.clean_if_not_none(row, 'date_planted')
            source = self.clean_if_not_none(row, 'source')
            if source is not None:
                source = PlantSourceType[source.upper()]
            if date_planted is not None:
                date_planted = datetime.datetime.strptime(date_planted, '%Y-%m-%d')
            with self.session_mgr() as session:
                plant = TablePlant(
                    species=self.get_species(common_name=common_name),
                    plant_source=source,
                    date_planted=date_planted,
                )
                session.add(plant)

    def load_scheduled_logs(self):
        pass
