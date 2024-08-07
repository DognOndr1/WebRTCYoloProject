from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
from typing import Any

if __name__ == "__main__":
    from webapp import WebServer
    from decorater import check_active_decorator
else:
    from app.webapp import WebServer
    from app.decorater import check_active_decorator


@dataclass
class FlaskWebServer(WebServer):
    """
    Flask tabanlı bir web sunucusu.
    Attributes:
        app (Flask): Flask uygulama nesnesi.
        logger (Any): Loglama için kullanılan logger nesnesi.
    Methods:
        server(): Flask uygulamasını başlatır ve ana sayfa rotasını tanımlar.
        run(): Sunucunun aktif olup olmadığını kontrol eder ve sunucuyu başlatır.
    """

    logger: Any = None

    def server(self):
        self.app = Flask(__name__)

        @self.app.route("/")
        def home():
            return render_template("index.html")

        @self.app.route("/api/time", methods=["POST"])
        def log_time():
            time_data = request.json
            self.logger.info(f"Received time: {time_data}")
            return jsonify({"Message": "Time received", "data": time_data})

        self.logger.info("Flask Başlatıldı")
        self.app.run(host=self.host, port=self.port, debug=self.debug)

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
        "127.0.0.1", 8000, True, True, logger=Logger(**logger_configs)
    )
    flaskwebserver.run()
