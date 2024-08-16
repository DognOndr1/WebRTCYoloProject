from flask import Flask, render_template, jsonify
from dataclasses import dataclass, field
from typing import Any
import logging

if __name__ == "__main__":
    from webapp import WebServer
    from decorater import check_active_decorator
else:
    from app.webapp import WebServer
    from app.decorater import check_active_decorator


@dataclass
class FlaskWebServer(WebServer):
    host: str
    port: int
    is_active: bool
    debug: bool
    logger: Any = field(default=None)

    def __post_init__(self):
        self.env: str = "local.toml"
        self.app = Flask(__name__)
        self.app.debug = self.debug

        if self.logger is None:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)

    def server(self):
        @self.app.route("/")
        def home():
            return render_template("index.html")

        @self.app.route("/framework")
        def get_framework():
            return jsonify({"framework": "flask"})

        self.logger.info("Flask Başlatıldı")
        self.app.run(host=self.host, port=self.port)

    @check_active_decorator
    def run(self):
        self.server()


if __name__ == "__main__":

    @dataclass
    class Logger:
        log_file: str
        log_format: str
        rotation: str

        def info(self, message: str):
            print(f"{message}")

    logger_configs = {
        "log_file": "logs/app.log",
        "log_format": "<green>{time:MMM D, YYYY - HH:mm:ss}</green> || <level>{level}</level> || <red>{file.name}</red> || <cyan>{message}</cyan>||",
        "rotation": "10MB",
    }

    flaskwebserver = FlaskWebServer(
        "0.0.0.0",
        8000,
        True,
        True,
        logger=Logger(**logger_configs),
    )
    flaskwebserver.run()
