#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from plant_tracker.config import DevelopmentConfig

if __name__ == '__main__':
    DevelopmentConfig().build_db_engine()
    from plant_tracker.app import create_app
    # Instantiate log here, as the hosts API is requested to communicate with influx
    app = create_app(config_class=DevelopmentConfig)
    app.run(host=DevelopmentConfig.DB_SERVER, port=DevelopmentConfig.PORT)
