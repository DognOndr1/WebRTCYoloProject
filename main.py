from app.fastapiweb import FastAPIWebServer
from app.flaskweb import FlaskWebServer
from app.config import ConfigLoader
from app.logs import Logger
import argparse


def main(config):
    
    server_params = {**config['Server'], **config['Static'], **config['Templates']}
    logger = Logger(**config['Logging']) 

    try:
           
        if config['API']['chosen_api'] == "Fast":
            server= FastAPIWebServer(**server_params,logger=logger )
            return server.run()
        if config['API']['chosen_api'] == "Flask":
            server = FlaskWebServer(**config['Server'],logger= logger)
            return server.run()
        return logger.warning("Yanlış API seçimi")
    
    except Exception as e:
        logger.error(f"Server Başlatılamadı: {str(e)}")
        
    
if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description="Select a configuration file for the application.")
    parser.add_argument(
        '--env',
        type=str,
        default="local.toml",
        help='Path to the configuration file. Choose between local.toml and prod.toml'
    )
    args = parser.parse_args()
    config = ConfigLoader(args.env).load_configs()
    main(config)
