from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template
)
import pandas as pd
from sqlalchemy.sql import distinct, func

from plant_tracker.model import (
    TablePlant,
    TablePlantHabit,
    TablePlantLocation,
    TablePlantSubRegion,
    TableSpecies
)
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng
)

bp_main = Blueprint('main', __name__)


@bp_main.route('/', methods=['GET'])
@bp_main.route('/home', methods=['GET'])
def index():
    eng = get_app_eng()
    with eng.session_mgr() as session:
        habits = session.query(
            TablePlantHabit.plant_habit,
            func.count(distinct(TableSpecies.species_id)),
            func.count(distinct(TablePlant.plant_id))
        )\
            .join(TableSpecies, TablePlantHabit.plant_habit_id == TableSpecies.habit_key)\
            .join(TablePlant, TableSpecies.species_id == TablePlant.species_key)\
            .group_by(TablePlantHabit.plant_habit).all()

        sources = session.query(
            TablePlant.plant_source,
            func.count(distinct(TableSpecies.species_id)),
            func.count(distinct(TablePlant.plant_id))
        ) \
            .join(TableSpecies, TablePlant.species_key == TableSpecies.species_id) \
            .group_by(TablePlant.plant_source).all()

        durations = session.query(
            TableSpecies.duration,
            func.count(distinct(TableSpecies.species_id)),
            func.count(distinct(TablePlant.plant_id))
        ) \
            .join(TablePlant, TablePlant.species_key == TableSpecies.species_id) \
            .group_by(TableSpecies.duration).all()
        zones = session.query(
            TablePlantSubRegion.sub_region_name,
            TablePlant.is_drip_irrigated,
            func.count(distinct(TablePlant.plant_id))
        ) \
            .join(TablePlantLocation, TablePlantLocation.sub_region_key == TablePlantSubRegion.sub_region_id) \
            .join(TablePlant, TablePlant.plant_location_key == TablePlantLocation.plant_location_id)\
            .group_by(
                TablePlantSubRegion.sub_region_name,
                TablePlant.is_drip_irrigated
            ).all()

    return render_template(
        'index.jinja',
        habit_data={
            'headers': ['Habit', 'Species', 'Plants'],
            'rows': [[*x] for x in habits]
        },
        source_data={
            'headers': ['Source', 'Species', 'Plants'],
            'rows': [[*x] for x in sources]
        },
        duration_data={
            'headers': ['Duration', 'Species', 'Plants'],
            'rows': [[*x] for x in durations]
        },
        zone_data={
            'headers': ['Zone', 'Is Irrigated', 'Plants'],
            'rows': [[*x] for x in zones]
        }
    )


@bp_main.route('/api/', methods=['GET'])
@bp_main.route('/api/home', methods=['GET'])
def get_app_info():
    return jsonify({
        'app_name': current_app.name,
        'version': current_app.config.get('VERSION')
    }), 200
