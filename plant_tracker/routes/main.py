from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template
)
import pandas as pd

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
        species_df = pd.read_sql(session.query(TableSpecies, TablePlantHabit.plant_habit).outerjoin(TablePlantHabit, TableSpecies.habit_key == TablePlantHabit.plant_habit_id).statement, session.connection())
        plants_df = pd.read_sql(session.query(TablePlant).statement, session.connection())
        mega_df = pd.merge(species_df, plants_df, left_on='species_id', right_on='species_key', how='left')

        habits = mega_df[['plant_habit', 'species_id', 'plant_id']].groupby('plant_habit').agg(
            {'species_id': pd.Series.nunique, 'plant_id': pd.Series.nunique}
        )

        sources = mega_df[['plant_source', 'species_id', 'plant_id']].groupby('plant_source').agg(
            {'species_id': pd.Series.nunique, 'plant_id': pd.Series.nunique}
        )

        durations = mega_df[['duration', 'species_id', 'plant_id']].groupby('duration').agg(
            {'species_id': pd.Series.nunique, 'plant_id': pd.Series.nunique}
        )

    return render_template(
        'index.jinja',
        habit_data={
            'headers': ['Habit', 'Species', 'Plants'],
            'rows': [[x[0], *x[1].to_list()] for x in habits.iterrows()]
        },
        source_data={
            'headers': ['Source', 'Species', 'Plants'],
            'rows':  [[x[0], *x[1].to_list()] for x in sources.iterrows()]
        },
        duration_data={
            'headers': ['Duration', 'Species', 'Plants'],
            'rows':  [[x[0], *x[1].to_list()] for x in durations.iterrows()]
        },
        # zone_data={
        #     'headers': ['Zone', 'Is Irrigated', 'Plants'],
        #     'rows': [[*x] for x in zones]
        # }
    )


@bp_main.route('/api/', methods=['GET'])
@bp_main.route('/api/home', methods=['GET'])
def get_app_info():
    return jsonify({
        'app_name': current_app.name,
        'version': current_app.config.get('VERSION')
    }), 200
