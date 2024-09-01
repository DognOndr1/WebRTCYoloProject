from fastapi import FastAPI, Request
import socketio, json, ssl
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dataclasses import dataclass
from typing import Any
import uvicorn, cv2
from fastapi.responses import JSONResponse
import cv2,os
import numpy as np

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCIceCandidate,
    VideoStreamTrack,
)
from av import VideoFrame
from aiortc.contrib.media import MediaRelay

if __name__ == "__main__":
    from detector import Detector
    from webapp import WebServer
    from decorater import check_active_decorator
else:
    from app.detector import Detector
    from app.webapp import WebServer
    from app.decorater import check_active_decorator


@dataclass
class FastAPIWebServer(WebServer):
    host: str
    port: int
    is_active: bool
    debug: bool
    static_directory: str = None
    temp_directory: str = None
    pcs: dict = None
    logger: Any = None
    socket_app: Any = None
    ssl_cert: str = None
    ssl_key: str = None

    def __post_init__(self):
        self.env: str = "local.toml"
        self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
        self.app = FastAPI()
        self.socket_app = socketio.ASGIApp(self.sio, self.app)
        self.relay = MediaRelay()
        self.app.mount(
            "/static", StaticFiles(directory=self.static_directory), name="static"
        )
        self.templates = Jinja2Templates(directory=self.temp_directory)
        if self.pcs is None:
            self.pcs = {}

    def server(self):
        @self.app.get("/")
        async def home(request: Request):
            return self.templates.TemplateResponse("index.html", {"request": request})

        @self.app.get("/framework")
        async def get_framework():
            return JSONResponse({"framework": "fastapi"})

        # Socket.IO dinleyicileri
        @self.sio.on("connect")
        async def connect(sid, env):
            
            self.logger.info("New Client Connected to This id :" + " " + str(sid))
            if sid in self.pcs:
                print(f"Existing connection for {sid} found, Closing it")
                await self.pcs[sid].close()
            self.pcs[sid] = RTCPeerConnection()

        @self.sio.on("disconnect")
        async def disconnect(sid):
            self.logger.info("Client disconnected: " + " " + str(sid))
            if sid in self.pcs:
                pc = self.pcs[sid]
                await pc.close()
                del self.pcs[sid]

        @self.sio.on("sdp")
        async def handle_sdp(sid, data):
            if sid in self.pcs:
                pc = self.pcs[sid]
                if pc.signalingState == "closed":
                    pc = RTCPeerConnection()
                    self.pcs[sid] = pc
            else:
                pc = RTCPeerConnection()
                self.pcs[sid] = pc

            offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
            self.logger.info("Received SDP offer")
            print(json.dumps(data, indent=2))

            @pc.on("track")
            def on_track(track):
                self.logger.info(f"Track received {track.kind}")
                if track.kind == "video":
                    print("Gray Track Mesajı")
                    gray_track = GrayVideoStreamTrack(self.relay.subscribe(track))
                    self.logger.info("Track added to PC")
                    pc.addTrack(gray_track)

            await pc.setRemoteDescription(offer)
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            print("Generated SDP answer")
            sdp_answer = json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
                indent=2,
            )
            print(sdp_answer)

            await self.sio.emit(
                "sdp_answer",
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
                to=sid,
            )

        @self.sio.on("ice_candidate")
        async def handle_ice_candidate(sid, data):
            self.logger.info("Received ICE Candidate")
            print(json.dumps(data, indent=2))

            if sid in self.pcs:
                pc = self.pcs[sid]
                try:
                    candidate_string = data.get("candidate", "")

                    if candidate_string:
                        parsed = parse_candidate(candidate_string)
                        candidate = RTCIceCandidate(
                            sdpMid=data.get("sdpMid"),
                            sdpMLineIndex=data.get("sdpMLineIndex"),
                            foundation=parsed["foundation"],
                            component=parsed["component"],
                            protocol=parsed["protocol"],
                            priority=parsed["priority"],
                            ip=parsed["ip"],
                            port=parsed["port"],
                            type=parsed["type"],
                        )
                        await pc.addIceCandidate(candidate)
                        print(f"Added ICE candidate for {sid}")
                    else:
                        print("Candidate string is empty.")
                except Exception as e:
                    print(f"Error adding ICE candidate for {sid}: {str(e)}")
                    print(f"Problematic data: {data}")
            else:
                print(f"No RTCPeerConnection found for sid: {sid}")

        module_directory = os.path.dirname(os.path.abspath(__file__))
        self.ssl_cert = os.path.join(module_directory, "..", "cert.pem")
        self.ssl_key = os.path.join(module_directory, "..", "key.pem")

        ssl_context = None
        if self.ssl_cert and self.ssl_key:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(certfile=self.ssl_cert, keyfile=self.ssl_key)

        self.logger.info("FastAPI started")
        uvicorn.run(
            self.socket_app,
            host=self.host,
            port=self.port,
            ssl_keyfile=self.ssl_key,
            ssl_certfile=self.ssl_cert,
        )

    @check_active_decorator
    def run(self):
        self.server()


class GrayVideoStreamTrack(VideoStreamTrack):
    def __init__(self, track):
        super().__init__()
        self.track = track
        self.detector = Detector()

    async def recv(self):
        frame = await self.track.recv()  # Alınan çerçeve
        if not isinstance(frame, VideoFrame):
            raise ValueError("Frame is not a VideoFrame")

        img = np.array(frame.to_ndarray(format="bgr24"))

        processed_frame = self.detector.process_frame(img)
        
        if processed_frame is None or not isinstance(processed_frame, np.ndarray):
            raise ValueError("Processed frame is None or not a numpy array")

        new_frame = VideoFrame.from_ndarray(processed_frame, format="bgr24")
        new_frame.time_base = frame.time_base
        new_frame.pts = frame.pts
        new_frame.dts = frame.dts
        return new_frame


def parse_candidate(candidate_str):
    parts = candidate_str.split()
    return {
        "foundation": parts[0].split(":")[1],
        "component": int(parts[1]),
        "protocol": parts[2].lower(),
        "priority": int(parts[3]),
        "ip": parts[4],
        "port": int(parts[5]),
        "type": parts[7],
    }


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

    module_directory = os.path.dirname(os.path.abspath(__file__))
    ssl_cert = os.path.join(module_directory, "..", "cert.pem")
    ssl_key = os.path.join(module_directory, "..", "key.pem")

    fastapiweb = FastAPIWebServer(
        "0.0.0.0",
        8000,
        True,
        True,
        static_directory="static",
        temp_directory="templates",
        logger=Logger(**logger_configs),
        ssl_cert=ssl_cert,
        ssl_key=ssl_key,
    )

    fastapiweb.run()
