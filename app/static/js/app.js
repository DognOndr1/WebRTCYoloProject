// !----------------------------------------------------------------STUN / TURN Sunucuları Ayarlanıyor----------------------------------------------------------------
const config = {
    iceServers: [
        {
            urls: 'stun:stun.l.google.com:19302' 
        }
    ]
};

// !----------------------------------------------------------------Kullanılacak Medya Akışları Belirleniyor----------------------------------------------------------------
const constraints = {
    video: { deviceId: undefined }, 
    audio: false
};

let pc = null;
let socket = null;
let stream = null;
let isStreaming = false;
let deviceType = getDeviceType();

// !----------------------------------------------------------------Cihaz Türünü Belirleme----------------------------------------------------------------
function getDeviceType() {
    const ua = navigator.userAgent;
    if (/mobile/i.test(ua)) {
        return 'mobile';
    }
    return 'desktop';
}

// !----------------------------------------------------------------HTML Elementleri Alınıyor----------------------------------------------------------------
const startBtn = document.querySelector("button#startButton");
const stopBtn = document.querySelector("button#stopButton");
const remoteVideo = document.querySelector("video.remoteVideo");
const logsContainer = document.querySelector(".logs");
const toggleButton = document.querySelector("#toggleButton");
const deviceSelect = document.getElementById("devices");

// !---------------------------------------------------------------Filtre Butonu CSS Özellikleri Ayarlanıyor----------------------------------------------------------------
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

const canvas = document.getElementById('canvas');
let ctx = canvas.getContext('2d');

// !----------------------------------------------------------------Canvas Boyutunu Güncelleme----------------------------------------------------------------
function updateCanvasSize() {
    const videoRect = remoteVideo.getBoundingClientRect();
    const videoWidth = videoRect.width;
    const videoHeight = videoRect.height;
    
    if (videoWidth === 0 || videoHeight === 0) return;

    canvas.width = videoWidth;
    canvas.height = videoHeight;
    canvas.style.width = videoWidth + 'px';
    canvas.style.height = videoHeight + 'px';
}

window.addEventListener('resize', updateCanvasSize);

remoteVideo.onloadedmetadata = () => {
    updateCanvasSize();
};

let mySID = null;

// !----------------------------------------------------------------Socket Bağlantısını Yapma----------------------------------------------------------------
function connectSocket() {
    socket = io(); 

    socket.on('connect', () => {
        mySID = socket.id; 
        console.log("My SID:", mySID);
        if (getBrowserInfo() === "Google Chrome") {
            cameraPermission()
        } else if (getBrowserInfo() === "Mozilla Firefox") {
            StartVideoForPerm()
            getConnectedDevices()
        }
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

    socket.on('detections', (data) => {
        try {
            const parsedData = JSON.parse(data);
            const detectionsArray = parsedData.detections;
            const originalWidth = parsedData.original_width;
            const originalHeight = parsedData.original_height;
    
            ctx.clearRect(0, 0, canvas.width, canvas.height);
    
            const scaleX = canvas.width / originalWidth;
            const scaleY = canvas.height / originalHeight;
    
            detectionsArray.forEach(detection => {
                if (detection.sid === mySID) {
                    const { bounding_box, confidence, class_id, class_name } = detection;

    
                    let { x1, y1, x2, y2 } = bounding_box;
    
                    x1 *= scaleX;
                    y1 *= scaleY;
                    x2 *= scaleX;
                    y2 *= scaleY;
    
                    ctx.strokeStyle = 'blue';
                    ctx.lineWidth = 2;
    
                    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

                    if (deviceType === "mobile") {
                        ctx.font = '12px Arial';
                        ctx.lineWidth = 1;
                    } else {
                        ctx.font = '16px Arial';
                        ctx.lineWidth = 2;
                    }
    
                    ctx.fillStyle = 'red';
    
                    const text = `ID: ${class_id}, ${class_name} Confidence: ${confidence.toFixed(2)}`;
                    ctx.fillText(text, x1, y1 > 20 ? y1 - 10 : y1 + 15);
                }
            });
        } catch (error) {
            console.error('Error parsing detections:', error);
        }
    });
}

// !----------------------------------------------------------------Video Görünümünü Duyarlı Yapma----------------------------------------------------------------
function responsiveVideo() {
    if (deviceType === "mobile") {
        remoteVideo.classList.remove("remoteVideoDesktop");
        remoteVideo.classList.add("remoteVideoMobile");
    } else {
        remoteVideo.classList.remove("remoteVideoMobile");
        remoteVideo.classList.add("remoteVideoDesktop");
    }
}

responsiveVideo()

// !----------------------------------------------------------------WebRTC İşlemleri Yapılıyor----------------------------------------------------------------
async function getMedia(deviceId) {
    try {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        
        if (pc) {
            pc.close();
        }

        constraints.video.deviceId = { exact: deviceId };
        
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        pc = new RTCPeerConnection(config);

        remoteVideo.srcObject = stream;
        remoteVideo.onloadedmetadata = () => {
            updateCanvasSize();
        };

        pc.oniceconnectionstatechange = () => {
            log("ICE connection state: " + pc.iceConnectionState);
        };

        pc.ontrack = (event) => {
            const incomingStream = event.streams[0];
            if (incomingStream) {
                if (remoteVideo.srcObject !== incomingStream) {
                    log("Remote video stream set");
                }
            } else {
                log("No streams available in the remote track event");
            }
        };

        stream.getTracks().forEach(track => pc.addTrack(track, stream));

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        
        log("Created and set local offer: " + JSON.stringify(offer));
        socket.emit('sdp', { type: offer.type, sdp: offer.sdp });

    } catch (error) {
        log("Error in getMedia: " + error, 'error');
    }
}

// !----------------------------------------------------------------Bağlı Cihazları Alma--------------------------------------------------------------------------------------
function getConnectedDevices() {
    navigator.mediaDevices.enumerateDevices()
    .then(devices => {
        const filtered = devices.filter(device => device.kind === 'videoinput');
        deviceSelect.innerHTML = ''; 
        filtered.forEach(device => {
            addOptionToSelect(device.label || `Camera ${filtered.indexOf(device) + 1}`, device.deviceId);
        });
    });
}

// !---------------------------------------------------------------Select Öğesine Seçenek Ekleme----------------------------------------------------------------
function addOptionToSelect(optionText, optionValue) {
    const option = document.createElement("option");
    option.text = optionText;
    option.value = optionValue;
    deviceSelect.appendChild(option);
}

// !----------------------------------------------------------------HTML Elementleri Alınıyor----------------------------------------------------------------
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

// !----------------------------------------------------------------Log Fonksiyonu--------------------------------------------------------------------------------------
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

// !-----------------------------------------------------------------Kamera İzni Kontrolü--------------------------------------------------------------------------------------
async function cameraPermission() {
    const result = await navigator.permissions.query({name: "camera"})

    if(result.state === "granted"){
        getConnectedDevices()
    }else{
        StartVideoForPerm()
        getConnectedDevices()
    }
}

// !-----------------------------------------------------------------Kamera İzni İçin Video Başlatma----------------------------------------------------------------
async function StartVideoForPerm() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({'video': true})
        stream.getTracks().forEach(track => track.stop())
    } catch (error) {
        console.log("Error: " + error)
    }
}

connectSocket()

// !-----------------------------------------------------------------Tarayıcı Bilgilerini Alma----------------------------------------------------------------
const userAgent = navigator.userAgent;
// !----------------------------------------------------------------Tarayıcı Adı ve Versiyonunu Bulma----------------------------------------------------------------
function getBrowserInfo() {
    if (userAgent.indexOf("Firefox") > -1) {
        return "Mozilla Firefox";
    } else if (userAgent.indexOf("SamsungBrowser") > -1) {
        return "Samsung Internet";
    } else if (userAgent.indexOf("Opera") > -1 || userAgent.indexOf("OPR") > -1) {
        return "Opera";
    } else if (userAgent.indexOf("Trident") > -1) {
        return "Internet Explorer";
    } else if (userAgent.indexOf("Edge") > -1) {
        return "Microsoft Edge";
    } else if (userAgent.indexOf("Chrome") > -1) {
        return "Google Chrome";
    } else if (userAgent.indexOf("Safari") > -1) {
        return "Safari";
    } else {
        return "Bilinmeyen Tarayıcı";
    }
}


