from app.fastapiweb import FastAPIWebServer
from app.flaskweb import FlaskWebServer
from app.config import ConfigLoader
from app.logs import Logger
from app.aiohttpweb import AIOHTTPWeb
import argparse

def main(config):
    logger = Logger(**config["Logging"])

    try:
        api_choice = config["API"]["chosen_api"]
        server_params = {
            **config["Server"],
            **config.get("Static", {}),
            **config.get("Templates", {}),
        }

        if api_choice == "Fast":
            server = FastAPIWebServer(
                **server_params,
                logger=logger,
                ssl_cert="./cert.pem",
                ssl_key="./key.pem",
            )
        elif api_choice == "Flask":
            server = FlaskWebServer(**server_params, logger=logger)
        elif api_choice == "aiohttp":
            server = AIOHTTPWeb(
                **server_params,
                logger=logger,
                ssl_cert="./cert.pem",
                ssl_key="./key.pem",
            )
        else:
            logger.warning("Invalid API choice")
            return

        server.run()

    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Select a configuration file for the application."
    )
    parser.add_argument(
        "--env",
        type=str,
        default="local.toml",
        help="Path to the configuration file. Choose between local.toml and prod.toml",
    )
    args = parser.parse_args()
    config = ConfigLoader(args.env).load_configs()
    main(config)
