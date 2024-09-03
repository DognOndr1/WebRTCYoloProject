import ssl, json, socketio, aiohttp_jinja2, jinja2
from typing import Any
from dataclasses import dataclass
from aiohttp import web
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCIceCandidate,
    VideoStreamTrack,
    RTCConfiguration,
    RTCIceServer,
)
from av import VideoFrame
from aiortc.contrib.media import MediaRelay
import numpy as np

if __name__ == "__main__":
    from detector import Detector
    from webapp import WebServer
    from decorater import check_active_decorator
else:
    from app.detector import Detector
    from app.webapp import WebServer
    from app.decorater import check_active_decorator


@dataclass
class AIOHTTPWeb(WebServer):

    def __post_init__(self):
        self.sio = socketio.AsyncServer(cors_allowed_origins="*")
        self.app = web.Application()
        self.sio.attach(self.app)
        self.relay = MediaRelay()
        aiohttp_jinja2.setup(
            self.app, loader=jinja2.FileSystemLoader(self.temp_directory)
        )
        if self.static_directory:
            self.app.router.add_static(
                "/static", path=self.static_directory, name="static"
            )
        if self.pcs is None:
            self.pcs = {}

    def register_socket_events(self):
        @self.sio.event
        async def connect(sid, environ):
            print(f"Client Connected {sid}")
            if sid in self.pcs:
                print(f"Existing connection for {sid} found. Closing it.")
                await self.pcs[sid].close()
            self.pcs[sid] = RTCPeerConnection(
                RTCConfiguration(
                    iceServers=[RTCIceServer("stun:stun.l.google.com:19302")]
                )
            )

        @self.sio.event
        async def disconnect(sid):
            print(f"Client Disconnected: {sid}")
            if sid in self.pcs:
                pc = self.pcs[sid]
                await pc.close()
                del self.pcs[sid]

        @self.sio.on("sdp")
        async def handle_sdp(sid, data):
            if sid in self.pcs:
                pc = self.pcs[sid]
                if pc.signalingState == "closed":
                    pc = RTCPeerConnection(
                        RTCConfiguration(
                            iceServers=[RTCIceServer("stun:stun.l.google.com:19302")]
                        )
                    )

                    self.pcs[sid] = pc
            else:
                pc = RTCPeerConnection(
                    RTCConfiguration(
                        iceServers=[RTCIceServer("stun:stun.l.google.com:19302")]
                    )
                )

                self.pcs[sid] = pc

            offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
            print("Received SDP offer")
            print(json.dumps(data, indent=2))

            @pc.on("track")
            def on_track(track):
                print(f"Track received: {track.kind}")
                if track.kind == "video":
                    object_detect = ObjectDetection(self.relay.subscribe(track),use_cuda=self.use_cuda)
                    pc.addTrack(object_detect)

            await pc.setRemoteDescription(offer)
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            print("Generated SDP answer:")
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
            print("Received ICE candidate")
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

    def server(self):
        async def home(request):
            return aiohttp_jinja2.render_template("index.html", request, {})

        async def get_framework(request):
            return web.json_response({"framework": "aiohttp"})
        
        async def get_obj(request):
            return web.json_response({"object_detection": self.object_detection})

        self.app.router.add_get("/", home)
        self.app.router.add_get("/framework", get_framework)
        self.app.router.add_get("/object_detect", get_obj)
        self.register_socket_events()


        ssl_context = None
        if self.ssl_cert and self.ssl_key:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(certfile="./cert.pem", keyfile="./key.pem")

        web.run_app(self.app, host=self.host, port=self.port, ssl_context=ssl_context)

    @check_active_decorator
    def run(self):
        self.server()


class ObjectDetection(VideoStreamTrack):
    def __init__(self, track,use_cuda):
        super().__init__()
        self.track = track
        self.detector = Detector(use_cuda=use_cuda)

    async def recv(self):
        frame = await self.track.recv() 
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

    web_server = AIOHTTPWeb(
        host="0.0.0.0",
        port=8000,
        is_active=True,
        debug=True,
        static_directory="static",
        temp_directory="templates",
        logger=None,
        pcs={},
        ssl_cert="../cert.pem",  
        ssl_key="../key.pem",
        object_detection=True,
        use_cuda=True
    )

    web_server.run()
