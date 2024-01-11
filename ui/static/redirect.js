//Request to call python functions
let xhr = null;
getXmlHttpRequestObject = function () {
    if (!xhr) {
        // Create a new XMLHttpRequest object
        xhr = new XMLHttpRequest();
    }
    return xhr;
};

function redirectToSearch() {
    console.log("Back to Search");
    window.location.href = "http://127.0.0.1:8000/views/";
}

//Slider JS
var inputRange = document.getElementsByClassName('range')[0],
    maxValue = 100, // the higher the smoother when dragging
    modValue = 0,
    speed = 5,
    currValue, rafID;

// set min/max value
inputRange.min = 0;
inputRange.max = maxValue;

// listen for unlock
function unlockStartHandler() {
    // clear raf if trying again
    window.cancelAnimationFrame(rafID);

    // set to desired value
    currValue = +this.value;
}

function unlockEndHandler() {

    // store current value
    currValue = +this.value;

    // determine if we have reached success or not
    if(currValue >= maxValue) {
        modMax();
    }
    if(currValue >= 25 && currValue < 50) {
        //rafID = window.requestAnimationFrame(animateHandler);
        modOne();
    }
    if(currValue >= 50 && currValue < 75) {
        modTwo();
    }
    if(currValue >= 75 && currValue < 100) {
        modThree();
    }
    else {
        rafID = window.requestAnimationFrame(animateHandler);
    }
}

// handle range animation
function animateHandler() {

    // calculate gradient transition
    var transX = currValue - maxValue;

    // update input range
    inputRange.value = currValue;

    // determine if we need to continue
    if(currValue > -1) {
      window.requestAnimationFrame(animateHandler);
    }
    if (currValue < 25) {
        // decrement value
        //currValue = currValue - speed;
        currValue = 0
    }
    if (currValue > 25) {
        currValue = 25;
    }
    if (currValue > 50) {
        currValue = 50;
    }
    if (currValue > 75) {
        currValue = 75;
    }
    else {
        // decrement value
        // currValue = currValue - speed;
    }
}


function modMax() {
    console.log("Most modified");
    modValue = 4;
}

function modOne() {
     console.log("Set to 1 mod ");
     modValue = 1;
}

function modTwo() {
     console.log("Set to 2 mod ");
     modValue = 2;
}

function modThree() {
     console.log("Set to 3 mod ");
     modValue = 3;
}

// bind events
inputRange.addEventListener('mousedown', unlockStartHandler, false);
inputRange.addEventListener('mousestart', unlockStartHandler, false);
inputRange.addEventListener('mouseup', unlockEndHandler, false);
inputRange.addEventListener('touchend', unlockEndHandler, false);

// move gradient
inputRange.addEventListener('input', function() {
    //Change slide thumb color on way up
    if (this.value < 25) {
        console.log("0 mods");
    }
    if (this.value > 25 && this.value < 50) {
        console.log("1 mods");
    }
    if (this.value > 50 && this.value < 75) {
        console.log("2 mods");
    }
    if (this.value > 75 && this.value < 100) {
        console.log("3 mods");
    }
});

//Hide loader after page has loaded
function hideLoader() {
    document.getElementById('loader').style.visibility = 'hidden';
}
//Show loading animation after searching and while page is loading
showLoader = function(e) {
    document.getElementById('loader').style.visibility = 'visible';
}

//Move user search result page
function sendToNewPage() {
    console.log("Sending user to new page");
    showLoader()
    // Check response is ready or not
    if (xhr.readyState === 4 || xhr.status === 201) {
        window.location.href = "http://127.0.0.1:8000/views/final-result";
        console.log("Received data");
        console.log(xhr.responseText);

    }
}

//Refactor and render links
let result_links = document.getElementsByClassName('result-link');
for (var i = 0; i < result_links.length; i++) {
    result_links[i].addEventListener('click', function(event) {
    // prevent navigating to a new page
    event.preventDefault();
    let inputValue = document.getElementById("search-input").innerHTML;
    let clickedLink = this.href;
    console.log('Clicked on: ' + clickedLink);
    console.log(inputValue)

    xhr = getXmlHttpRequestObject();
    xhr.onreadystatechange = sendToNewPage;

    xhr.open("POST", "http://127.0.0.1:8000/views/final-result", true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    // Send the request over the network
    xhr.send(JSON.stringify({"data": inputValue,  "pref-website": clickedLink}));

    // if (clickedLink === 'youtube.come') {
    //
    // }
  });
}
