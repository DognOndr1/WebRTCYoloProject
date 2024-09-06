from fastapi import FastAPI, Request
import socketio, json
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dataclasses import dataclass
import uvicorn
from fastapi.responses import JSONResponse
import numpy as np
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCIceCandidate,
    VideoStreamTrack,
)
from aiortc.contrib.media import MediaRelay
from av import VideoFrame

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
        self.data_channels = {}  # Her sid için bir DataChannel tutacağız

    def server(self):
        @self.app.get("/")
        async def home(request: Request):
            return self.templates.TemplateResponse("index.html", {"request": request})

        @self.app.get("/object_detect")
        async def get_framework():
            return JSONResponse({"object_detection": self.object_detection})

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
            if sid in self.data_channels:
                del self.data_channels[sid]

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

            dc = pc.createDataChannel(f"detections_{sid}")
            self.data_channels[sid] = dc

            @pc.on("track")
            def on_track(track):
                self.logger.info(f"Track received {track.kind}")
                if track.kind == "video":
                    print("Object Track Mesajı")
                    object_track = ObjectDetection(self.relay.subscribe(track), self.data_channels[sid], sid=sid, use_cuda=self.use_cuda)
                    self.logger.info("Track added to PC")
                    pc.addTrack(object_track)

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

        @self.sio.on("video_dimensions")
        async def video_dimensions(sid, data):
            print(f"Received video dimensions from {sid}: {data}")
        

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


class ObjectDetection(VideoStreamTrack):
    def __init__(self, track, data_channel, sid, use_cuda):
        super().__init__()
        self.track = track
        self.detector = Detector(use_cuda=use_cuda,filter_classes = [0,1])
        self.data_channel = data_channel
        self.sid = sid

    async def recv(self):
        frame = await self.track.recv()
        if not isinstance(frame, VideoFrame):
            raise ValueError("Frame is not a VideoFrame")

        img = np.array(frame.to_ndarray(format="bgr24"))

        detections, original_width, original_height = self.detector.process_frame(img)

        if detections:
            for detection in detections:
                detection['sid'] = self.sid

            data_to_send = {
                'detections': detections,
                'original_width': original_width,
                'original_height': original_height
            }
        else:
            data_to_send = {
                'detections': 0,
                'original_width': original_width,
                'original_height': original_height
            }

        if self.data_channel.readyState == "open":
            self.data_channel.send(json.dumps(data_to_send))
        else:
            print(f"Data channel for {self.sid} is not open")

        return frame

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

    fastapiweb = FastAPIWebServer(
        "0.0.0.0",
        8000,
        True,
        True,
        static_directory="static",
        temp_directory="templates",
        logger=Logger(**logger_configs),
        ssl_cert="../cert.pem",
        ssl_key="../key.pem",
        object_detection=True,
        use_cuda=True
    )
    

    fastapiweb.run()