from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dataclasses import dataclass
from typing import Any
import uvicorn
from pydantic import BaseModel

if __name__ == "__main__":
    from decorater import check_active_decorator
else:
    from app.decorater import check_active_decorator


class TimeData(BaseModel):
    hours: int
    minutes: int
    seconds: int


@dataclass
class FastAPIWebServer:
    host: str
    port: int
    is_active: bool
    debug: bool
    static_directory: str = None
    temp_directory: str = None
    logger: Any = None

    def __post_init__(self):
        self.env: str = "local.toml"
        self.app = FastAPI()
        self.app.mount(
            "/static", StaticFiles(directory=self.static_directory), name="static"
        )
        self.templates = Jinja2Templates(directory=self.temp_directory)

    def server(self):
        @self.app.get("/", response_class=HTMLResponse)
        def home(request: Request):
            return self.templates.TemplateResponse("index.html", {"request": request})

        @self.app.post("/api/time")
        def log_time(request: Request, time_data: TimeData):
            self.logger.info(
                f"Received time: {time_data.hours}:{time_data.minutes}:{time_data.seconds}"
            )
            return {"message": "Time received successfully"}

        self.logger.info("FastAPI başlatıldı")
        uvicorn.run(self.app, host=self.host, port=self.port)

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
            print(f"INFO: {message}")

    logger_configs = {
        "log_file": "logs/app.log",
        "log_format": "<green>{time:MMM D, YYYY - HH:mm:ss}</green> || <level>{level}</level> || <red>{file.name}</red> || <cyan>{message}</cyan>||",
        "rotation": "10MB",
    }

    fastapiweb = FastAPIWebServer(
        "127.0.0.1",
        8000,
        True,
        True,
        static_directory="static",
        temp_directory="templates",
        logger=Logger(**logger_configs),
    )

    fastapiweb.run()
