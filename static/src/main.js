let resultImage = document.getElementById("resultImage");
let canvas = document.getElementById('canvas');
let context = canvas.getContext('2d');
let imageLoaded = false;
let intervalId = null;
let isDrawing = false;
let points = [];



window.onload = function() {
};

function adjustCanvasSize() {
    canvas.width = resultImage.width;
    canvas.height = resultImage.height;
    canvas.style.width = resultImage.clientWidth + 'px';
    canvas.style.height = resultImage.clientHeight + 'px';
}

resultImage.addEventListener('load', () => {
    imageLoaded = true
    adjustCanvasSize();
})

document.getElementById("sendPolygon").addEventListener("click", function() {
    if (points.length > 2) {
        context.clearRect(0, 0, canvas.width, canvas.height)
        $.ajax({
            type: 'POST',
            url: '/_send_polygon',
            data: JSON.stringify({ polygon: points }),
            contentType: 'application/json',
            success: function(response) {
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });
    }

});

function resetPolygon() {
    points = [];
    context.clearRect(0, 0, canvas.width, canvas.height);
}

document.getElementById("resetPolygon").addEventListener("click", function() {
    resetPolygon();
});

canvas.addEventListener('mousedown', (e) => {
    if(imageLoaded) {
        isDrawing = true;
        const x = e.offsetX;
        const y = e.offsetY;
        if(points.length === 0) {
            points.push({ x, y });
        }
        points.push({ x, y });
    }
});

function drawLines() {
    context.clearRect(0, 0, canvas.width, canvas.height);

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

canvas.addEventListener('mousemove', (e) => {
    if (isDrawing) {
        const x = e.offsetX;
        const y = e.offsetY;
        points[points.length - 1] = { x, y }; // Update the last point
        drawLines();
    }
});

canvas.addEventListener('mouseup', () => {
    if (isDrawing) {
        isDrawing = false;
    }
});

canvas.addEventListener('mouseout', () => {
    isDrawing = false;
});

function getImage() {
    resultImage.setAttribute('src', "video_feed")
}

function clearImage() {
    resultImage.setAttribute("src", "")
}

$(document).ready(function() {
    $('#userInput').keypress(function(event) {
        if (event.key === 'Enter') {
            resetPolygon()
            let inputValue = $(this).val();
            $.ajax({
                type: 'POST',
                url: '/_send_camera_ip',
                data: JSON.stringify({ camera_ip: inputValue }),
                contentType: 'application/json',
                success: function(response) {
                    console.log(response.action)
                    if (response.action === 'not_found') {
                        $('.Notification').html('Not found');
                        clearImage()
                    } else if (response.action === 'access_camera_success') {
                        $('.Notification').html('');
                        getImage()
                    }
                },
                error: function(error) {
                    console.error('Error sending value:', error);
                }
            });
        }
    });
});

document.getElementById('modelForm').addEventListener('change', function(event) {
    if (event.target.name === 'choice') {
        const selectedValue = event.target.value;
        fetch('/_submit_model_choice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ choice: selectedValue })
        })
        .then(response => {
            data = response.json()
            console.log('Success:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }
});
