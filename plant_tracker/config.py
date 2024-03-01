"""Configuration setup"""
from importlib import metadata
import os
import pathlib
import random
import string
from typing import Dict

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from plant_tracker.model import Base


HOME = pathlib.Path().home()
KEY_DIR = HOME.joinpath('keys')
LOG_DIR = HOME.joinpath('logs')


def get_local_secret_key(path: pathlib.Path) -> str:
    """Grabs a locally-stored secret"""
    if not path.exists():
        raise FileNotFoundError(f'The secret key was not found at path: {path}')
    with path.open() as f:
        return f.read().strip()


def read_secrets(path_obj: pathlib.Path) -> Dict:
    secrets = {}
    with path_obj.open('r') as f:
        for item in f.readlines():
            if item.startswith('#'):
                continue
            k, v = item.split('=', 1)
            secrets[k] = v.strip()
    return secrets


class BaseConfig(object):
    """Configuration items common across all config types"""
    ENV = 'DEV'
    DEBUG = False
    TESTING = False

    VERSION = metadata.version('plant-tracker')
    PORT = 5010
    # Stuff for frontend
    STATIC_DIR_PATH = '../static'
    TEMPLATE_DIR_PATH = '../templates'

    DATA_DIR = HOME.joinpath('data/plant-tracker')
    DATA_DIR.mkdir(exist_ok=True)

    BACKUP_DIR = DATA_DIR.joinpath('backups')
    BACKUP_DIR.mkdir(exist_ok=True)

    # backend
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{usr}:{pwd}@{host}:{port}/{database}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRETS = None
    ENGINE = None
    SESSION = None

    @classmethod
    def load_secrets(cls):
        if cls.ENV == 'DEV':
            secrets_path = pathlib.Path(__file__).parent.parent.joinpath('secretprops.properties')
        else:
            secrets_path = KEY_DIR.joinpath('plants-secretprops.properties')
        cls.SECRETS = read_secrets(secrets_path)

    @classmethod
    def build_db_engine(cls):
        """Builds database engine, sets SESSION"""
        if cls.SECRETS is None:
            cls.load_secrets()
        cls.SQLALCHEMY_DATABASE_URI = cls.SQLALCHEMY_DATABASE_URI.format(**cls.SECRETS)
        engine = create_engine(cls.SQLALCHEMY_DATABASE_URI, isolation_level='SERIALIZABLE')
        Base.metadata.bind = engine
        cls.ENGINE = engine
        cls.SESSION = sessionmaker(bind=engine)

    SECRET_KEY_PATH = KEY_DIR.joinpath('plant-tracker-secret')
    if not SECRET_KEY_PATH.exists():
        logger.info('SECRET_KEY not detected. Writing a new one.')
        SECRET_KEY = ''.join(random.choice(string.ascii_lowercase) for i in range(32))
        with SECRET_KEY_PATH.open('w') as f:
            f.write(SECRET_KEY)
    else:
        SECRET_KEY = get_local_secret_key(SECRET_KEY_PATH)


class DevelopmentConfig(BaseConfig):
    """Configuration for development environment"""
    ENV = 'DEV'
    DEBUG = True
    DB_SERVER = 'localhost'
    LOG_LEVEL = 'DEBUG'

    def __init__(self):
        os.environ['PT_ENV'] = self.ENV


class ProductionConfig(BaseConfig):
    """Configuration for production environment"""
    ENV = 'PROD'
    DEBUG = False
    DB_SERVER = '0.0.0.0'
    LOG_LEVEL = 'DEBUG'

    def __init__(self):
        os.environ['PT_ENV'] = self.ENV
