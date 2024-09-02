/*
    * -----------------------------------------------------------------------STUN / TURN Sunucuları Ayarlanıyor --------------------------------------------------------------------
*/
const config = {
    iceServers: [
        {
            urls: 'stun:stun.l.google.com:19302' 
        }
    ]
};


/*
    * -----------------------------------------------------------------------Kullanılacak Medya Akışları Belirleniyor --------------------------------------------------------------------
*/
const constraints = {
    video: { deviceId: undefined }, 
    audio: false
};

let pc = null;
let socket = null;
let stream = null;
let isStreaming = false;
let object_detection = null


/*
    * -----------------------------------------------------------------------HTML Elementleri ALınıyor --------------------------------------------------------------------
*/
const startBtn = document.querySelector("button#startButton");
const stopBtn = document.querySelector("button#stopButton");
const remoteVideo = document.querySelector("video#remoteVideo");
const logsContainer = document.querySelector(".logs");
const toggleButton = document.querySelector("#toggleButton");
const deviceSelect = document.getElementById("devices");
const detectorSection = document.querySelector(".detector-section")
const videoSection = document.querySelector(".video-sec");


/*
    * ----------------------------------------------------------Kullanılarn Frameworke Göre Arayüz Ayarlanıyor --------------------------------------------------------------------
*/

fetch('/object_detect')   
    .then(response => response.json())  
    .then(data => { 
        console.log(data)
            object_detection = data.object_detection
        })  
    .catch(error => { 
            console.error("Error fetching object detection status:", error); 
    });


connectSocket();
getConnectedDevices();


/*
    * ---------------------------------------------------------------Filtre Butonu CSS Özellikleri Ayarlanıyor --------------------------------------------------------------------
*/
async function toggleStream() {
    if (isStreaming) {
        await stop();
        toggleButton.textContent = "Start Video";
        isStreaming = false;
        toggleButton.classList.remove("bg-danger");
    } else {
        await start();
        toggleButton.textContent = "Stop Video";
        isStreaming = true;
        toggleButton.classList.add("bg-danger");
    }
}


/*
    * ----------------------------------------------------------------------Socket IO Ayarları Yapılıyor --------------------------------------------------------------------
*/
function connectSocket() {
    socket = io(); 

    socket.on('connect', () => {
        log('Connected to server');
    });

    socket.on('disconnect', () => {
        log('Disconnected from server');
    });

    socket.on('ice_candidate', async (candidate) => {
        log("Received ICE candidate from server: " + JSON.stringify(candidate));
        try {
            const rtcCandidate = new RTCIceCandidate(candidate);
            await pc.addIceCandidate(rtcCandidate);
            log("Successfully added ICE candidate from server");
        } catch (error) {
            log("Error adding received ICE candidate: " + error, 'error');
        }
    });

    socket.on('sdp_answer', async (answer) => {
        log("Received SDP Answer from server: " + JSON.stringify(answer));
        try {
            await pc.setRemoteDescription(new RTCSessionDescription(answer));
            log("Set Remote Answer");
        } catch (error) {
            log("Error setting remote description: " + error, 'error');
        }
    });
}


/*
    * -----------------------------------------------------------------------WebRTC İşlemleri Yapılıyor--------------------------------------------------------------------
*/
async function getMedia(deviceId) {
    try {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }

        if (pc) {
            pc.close();
            pc = null;
        }

        constraints.video.deviceId = { exact: deviceId };

        stream = await navigator.mediaDevices.getUserMedia(constraints);

        if (object_detection === true) {
            startWebRTC();
        } else {
            remoteVideo.srcObject = stream
            log("Object detection is disabled. Video is only displayed locally.");
        }

    } catch (error) {
        log("Error in getMedia: " + error, 'error');
    }
}

function startWebRTC() {
    pc = new RTCPeerConnection(config);

    pc.oniceconnectionstatechange = () => {
        log("ICE connection state: " + pc.iceConnectionState);
    };

    pc.onicecandidate = (event) => {
        if (event.candidate) {
            console.log("New ICE candidate:", JSON.stringify(event.candidate, null, 2));
            log("New ICE candidate: " + JSON.stringify(event.candidate, null, 2));
            socket.emit('ice_candidate', event.candidate);
        }
    };

    pc.ontrack = (event) => {
        const incomingStream = event.streams[0];
        if (incomingStream) {
            if (remoteVideo.srcObject !== incomingStream) {
                remoteVideo.srcObject = incomingStream
                log("Remote video stream set");
            }
        } else {
            log("No streams available in the remote track event");
        }
    };

    stream.getTracks().forEach(track => pc.addTrack(track, stream));

    pc.createOffer().then(offer => {
        return pc.setLocalDescription(offer);
    }).then(() => {
        log("Created and set local offer: " + JSON.stringify(pc.localDescription));
        socket.emit('sdp', { type: pc.localDescription.type, sdp: pc.localDescription.sdp });
    }).catch(error => {
        log("Error creating or setting local description: " + error, 'error');
    });
}


/*
    * -----------------------------------------------------------------------Bağlı ve Dahili Medya Cihazları --------------------------------------------------------------------
*/
function getConnectedDevices() {
    navigator.mediaDevices.enumerateDevices()
    .then(devices => {
        const filtered = devices.filter(device => device.kind === 'videoinput');
        deviceSelect.innerHTML = ''; // Clear existing options
        filtered.forEach(device => {
            addOptionToSelect(device.label || `Camera ${filtered.indexOf(device) + 1}`, device.deviceId);
        });
    });
}

///////////////////////
function addOptionToSelect(optionText, optionValue) {
    const option = document.createElement("option");
    option.text = optionText;
    option.value = optionValue;
    deviceSelect.appendChild(option);
}


/*
    * -----------------------------------------------------------------------HTML Elementleri ALınıyor --------------------------------------------------------------------
*/
async function start() {
    try {
        if (pc) {
            pc.close();
            pc = null;
        }
        const selectedDeviceId = deviceSelect.value; // Seçilen Medya Cihazı ID'sini Alma
        if (selectedDeviceId) {
            await getMedia(selectedDeviceId);
            log("Video stream started");
        } else {
            log("No video device selected", 'warning');
        }
    } catch (error) {
        log("Error starting the connection: " + error, 'error');
    }
}

function stop() {
    log("Stopping Video");
    logsContainer.innerHTML = "";

    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }

    if (pc) {
        pc.close();
        pc = null;
    }

    remoteVideo.srcObject = null;
    log("Video stream stopped");
}




toggleButton.addEventListener("click", toggleStream);

log("Script loaded. Click the start button to begin.");

/*
    * -----------------------------------------------------------------------HTML Elementleri ALınıyor --------------------------------------------------------------------
*/

function log(message, level = 'info') {
    console.log(message);

    const logEntry = document.createElement('p');
    logEntry.textContent = message;

    switch (level) {
        case 'error':
            logEntry.className = 'log-error';
            break;
        case 'warning':
            logEntry.className = 'log-warning';
            break;
        default:
            logEntry.className = 'log-info';
            break;
    }

    logsContainer.appendChild(logEntry);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}