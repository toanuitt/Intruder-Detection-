
let video = document.querySelector("#videoElement");
let canvas = document.getElementById('canvas');
let context = canvas.getContext('2d');
let isCameraOn = false;
let isSendingFrames = false;
let intervalId = null;

// Access the camera
function startCamera() {
    if (navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                video.srcObject = stream;
                isCameraOn = true;
            })
            .catch(function(error) {
                console.log("Something went wrong");
            });
    } else {
        console.log("Media not supported");
    }
}

// Stop sending frames to backend
function stopSendingFrames() {
    isSendingFrames = false;
    clearInterval(intervalId);
}

// Send frame to backend
function sendFrame() {
    if (!isSendingFrames) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    let dataURL = canvas.toDataURL('image/jpeg');
    $.ajax({
        type: "POST",
        url: "/_photo_cap",
        data: { photo_cap: dataURL },
        success: function(response) {
            console.log(response.response);
            $('#resultContainer').html(response.message);
        },
        error: function(error) {
            console.log(error);
        },
        complete: function() {
            intervalId = setTimeout(sendFrame, 100); // Send the next frame after a short delay
        }
    });
}

// Initialize camera and canvas size
window.onload = function() {
    startCamera();
};

video.addEventListener('loadedmetadata', () => {
    adjustCanvasSize();
});

document.getElementById("startSendingFrames").addEventListener("click", function() {
    if (!isSendingFrames) {
        isSendingFrames = true;
        sendFrame();
        document.getElementById("startSendingFrames").textContent = "Stop Sending Frames";
    } else {
        stopSendingFrames();
        document.getElementById("startSendingFrames").textContent = "Start Sending Frames";
    }
});

document.getElementById("resetPolygon").addEventListener("click", function() {
    resetPolygon();
});

function adjustCanvasSize() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.style.width = video.clientWidth + 'px';
    canvas.style.height = video.clientHeight + 'px';
}

let isDrawing = false;
let points = [];

canvas.addEventListener('mousedown', (e) => {
    isDrawing = true;
    const x = e.offsetX;
    const y = e.offsetY;
    points.push({ x, y });
});

canvas.addEventListener('mousemove', (e) => {
    if (isDrawing) {
        const x = e.offsetX;
        const y = e.offsetY;
        points.push({ x, y });
        drawPolyline();
    }
});

canvas.addEventListener('mouseup', () => {
    isDrawing = false;
    sendPolygonPoints(); // Send points to the backend when drawing is complete
});

canvas.addEventListener('mouseout', () => {
    isDrawing = false;
});

function drawPolyline() {
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.drawImage(video, 0, 0, canvas.width, canvas.height); // Redraw the video frame
    if (points.length < 2) return;

    context.beginPath();
    context.moveTo(points[0].x, points[0].y);

    for (let i = 1; i < points.length; i++) {
        context.lineTo(points[i].x, points[i].y);
    }

    context.strokeStyle = 'red';
    context.lineWidth = 2;
    context.stroke();
}

function resetPolygon() {
    points = [];
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.drawImage(video, 0, 0, canvas.width, canvas.height); // Redraw the video frame
}

function sendPolygonPoints() {
    $.ajax({
        type: "POST",
        url: "/_send_polygon",
        contentType: "application/json",
        data: JSON.stringify({ points: points }),
        success: function(response) {
            console.log(response);
        },
        error: function(error) {
            console.log(error);
        }
    });
}
$(document).ready(function() {
    $('#userInput').keypress(function(event) {
        if (event.key === 'Enter') {
            $(this).val(0);
        }
    });
});
