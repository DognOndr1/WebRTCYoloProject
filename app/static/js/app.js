function Clock() {
    const time = new Date();
    const hours = time.getHours();
    const minutes = time.getMinutes();
    const seconds = time.getSeconds();

    let currentTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    document.getElementById('clock').textContent = currentTime;

    let timeData = { 
        hours: hours, 
        minutes: minutes, 
        seconds: seconds 
    };


    fetch('http://127.0.0.1:8000/api/time', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(timeData),
    })
    .then(response => response.json())
    .then(data => {
        console.log("Success:", data);
    })
    .catch((error) => {
        console.log("Error:", error);
    });
}

setInterval(Clock,1000);
Clock();

console.log("Hello World")