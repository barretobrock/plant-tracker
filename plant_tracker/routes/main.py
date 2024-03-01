from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template
)

bp_main = Blueprint('main', __name__)


@bp_main.route('/', methods=['GET'])
@bp_main.route('/home', methods=['GET'])
def index():
    return render_template('index.html')


@bp_main.route('/api/', methods=['GET'])
@bp_main.route('/api/home', methods=['GET'])
def get_app_info():
    return jsonify({
        'app_name': current_app.name,
        'version': current_app.config.get('VERSION')
    }), 200
