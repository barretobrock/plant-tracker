from flask import (
    Flask,
    Response,
    jsonify,
    request,
)
from flask_cors import CORS
from pukr import (
    InterceptHandler,
    get_logger,
)
from werkzeug.exceptions import HTTPException
from werkzeug.http import HTTP_STATUS_CODES

from plant_tracker.config import DevelopmentConfig
from plant_tracker.core.db import DBAdmin
from plant_tracker.flask_base import db
from plant_tracker.routes.family import bp_family
from plant_tracker.routes.helpers import (
    clear_trailing_slash,
    get_app_logger,
    log_after,
    log_before,
)
from plant_tracker.routes.main import bp_main
from plant_tracker.routes.plants import bp_plant
from plant_tracker.routes.species import bp_species


ROUTES = [
    bp_family,
    bp_main,
    bp_plant,
    bp_species
]


def handle_err(err):
    _log = get_app_logger()
    _log.error(err)
    if err.code == 404:
        _log.error(f'Path requested: {request.path}')

    if isinstance(err, HTTPException):
        err_msg = getattr(err, 'description', HTTP_STATUS_CODES.get(err.code, ''))
        return jsonify({'message': err_msg}), err.code
    if not getattr(err, 'message', None):
        return jsonify({'message': 'Server has encountered an error.'}), 500
    return jsonify(**err.kwargs), err.http_status_code


def create_app(*args, **kwargs) -> Flask:
    """Creates a Flask app instance"""
    # Config app, default to development if not provided
    config_class = kwargs.pop('config_class', DevelopmentConfig)
    config_class.build_db_engine()

    app = Flask(__name__, static_url_path='/')
    CORS(app)
    app.config.from_object(config_class)
    # Reduce the amount of 404s by disabling strict slashes (e.g., when a forward slash is appended to a url)
    app.url_map.strict_slashes = False

    # Initialize database ops
    db.init_app(app)

    # Initialize logger
    logger = get_logger(app.config.get('NAME'), log_dir_path=app.config.get('LOG_DIR'),
                        show_backtrace=app.config.get('DEBUG'), base_level=app.config.get('LOG_LEVEL'))
    logger.info('Logger started. Binding to app handler...')
    app.logger.addHandler(InterceptHandler(logger=logger))
    # Bind logger so it's easy to call from app object in routes
    app.extensions.setdefault('logg', logger)

    # Register routes
    logger.info('Registering routes...')
    for ruut in ROUTES:
        app.register_blueprint(ruut)

    for err_code, name in HTTP_STATUS_CODES.items():
        if err_code >= 400:
            try:
                app.register_error_handler(err_code, handle_err)
            except ValueError:
                pass

    app.config['db'] = db

    eng = DBAdmin(log=logger, env=config_class.ENV, tables=[])
    app.extensions.setdefault('eng', eng)

    app.before_request(log_before)
    app.before_request(clear_trailing_slash)
    # app.before_request(handle_preflight)
    app.after_request(log_after)
    # app.after_request(set_headers)

    return app
