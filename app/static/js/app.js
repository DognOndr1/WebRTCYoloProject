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
let object_detection = false
let dc, dcInterval = null

const loader = document.querySelector(".loading");

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

fetch('/object_detect')   
    .then(response => response.json())  
    .then(data => { 
        console.log(data)
            object_detection = data.object_detection
        })  
    .catch(error => { 
            console.error("Error fetching object detection status:", error); 
    });

let mySID = null;

// !----------------------------------------------------------------Socket Bağlantısını Yapma----------------------------------------------------------------
function connectSocket() {
    socket = io(); 

    socket.on('connect', () => {
        mySID = socket.id; 
        console.log("My SID:", mySID);
        cameraPermission();
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

                    if(delay === false){
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
            pc = null;
        }

        constraints.video.deviceId = { exact: deviceId };

        stream = await navigator.mediaDevices.getUserMedia(constraints);
        remoteVideo.srcObject = stream;
        remoteVideo.onloadedmetadata = () => {
            updateCanvasSize();
        };

        if (object_detection === true) {
            startWebRTC();
        } else {
            log("Object detection is disabled. Video is only displayed locally.");
        }

    } catch (error) {
        log("Error in getMedia: " + error, 'error');
    }
}

function startWebRTC() {
    pc = new RTCPeerConnection(config);

    var time_start = null;

    const current_stamp = () => {
        if (time_start === null) {
            time_start = new Date().getTime();
            return 0;
        } else {
            return new Date().getTime() - time_start;
        }
    };
    
    dc = pc.createDataChannel('chat');

    // DataChannel kapandığında interval temizleniyor
    dc.addEventListener('close', () => {
        console.log('DataChannel kapandı');
        clearInterval(dcInterval);
    });
    
    // DataChannel açıldığında, ping mesajları gönderiliyor
    dc.addEventListener('open', () => {
        console.log('DataChannel açıldı');
        dcInterval = setInterval(() => {
            var message = 'ping ' + current_stamp();
            console.log('Ping mesajı gönderildi: ' + message);
            dc.send(message);
        }, 1);
    });
    
    // DataChannel üzerinden mesaj alındığında
    dc.addEventListener('message', (evt) => {
        console.log('Mesaj alındı: ' + evt.data);
    
        if (evt.data.substring(0, 4) === 'pong') {
            var elapsed_ms = current_stamp() - parseInt(evt.data.substring(5), 10);
            console.log('Pong mesajı alındı, gecikme süresi: ' + elapsed_ms + ' ms');
        }
    });

    
    
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

// !----------------------------------------------------------------Bağlı Cihazları Alma--------------------------------------------------------------------------------------
async function getConnectedDevices() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const filtered = devices.filter(device => device.kind === 'videoinput');
        deviceSelect.innerHTML = ''; 
        filtered.forEach(device => {
            addOptionToSelect(device.label || `Camera ${filtered.indexOf(device) + 1}`, device.deviceId);
        });
        
        // Eğer hiç kamera bulunamazsa, kullanıcıya bilgi ver
        if (filtered.length === 0) {
            log("No cameras found. Please check your camera permissions and connections.", 'warning');
        } else {
            log("Cameras listed successfully.");
        }
    } catch (error) {
        console.log("Error enumerating devices: " + error);
        log("Error listing cameras. Please refresh the page and try again.", 'error');
    }
}

// !---------------------------------------------------------------Select Öğesine Seçenek Ekleme----------------------------------------------------------------
function addOptionToSelect(optionText, optionValue) {
    const option = document.createElement("option");
    option.text = optionText;
    option.value = optionValue;
    deviceSelect.appendChild(option);
}

let delay;
let timeoutId;

// !----------------------------------------------------------------HTML Elementleri Alınıyor----------------------------------------------------------------
async function start() {
    try {
        if (pc) {
            pc.close();
            pc = null;
        }
        const selectedDeviceId = deviceSelect.value;
        if (selectedDeviceId) {
            await getMedia(selectedDeviceId);
            log("Video stream started");

            loader.classList.add("loader");

            timeoutId = setTimeout(() => {
                loader.classList.remove("loader");
                delay = false; // Allow detection drawing
                log("Detection started after 5 seconds");
            }, 10000);
            
        } else {
            log("No video device selected", 'warning');
        }
        canvas.style.opacity = "1";
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
    loader.classList.remove("loader");
    clearTimeout(timeoutId);
    remoteVideo.srcObject = null;
    delay = true;
    log("Video stream stopped");
    canvas.style.opacity = "0";
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
    try {
        const result = await navigator.permissions.query({name: "camera"})
        if(result.state === "granted"){
            await getConnectedDevices()
        } else {
            await StartVideoForPerm()
        }
    } catch (error) {
        console.log("Error checking camera permission: " + error)
        await StartVideoForPerm()
    }
}

// !-----------------------------------------------------------------Kamera İzni İçin Video Başlatma----------------------------------------------------------------
async function StartVideoForPerm() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({'video': true})
        stream.getTracks().forEach(track => track.stop())
        // İzin alındıktan sonra cihazları yeniden listele
        await getConnectedDevices()
    } catch (error) {
        console.log("Error getting camera permission: " + error)
    }
}

connectSocket()