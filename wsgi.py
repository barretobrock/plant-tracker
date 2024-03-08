from plant_tracker.config import ProductionConfig

if __name__ == '__main__':
    ProductionConfig().build_db_engine()
    from plant_tracker.app import create_app

    # Instantiate log here, as the hosts API is requested to communicate with influx
    app = create_app(config_class=ProductionConfig)
    app.run(host=ProductionConfig.DB_SERVER, port=ProductionConfig.PORT)
