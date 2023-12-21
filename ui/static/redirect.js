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
    if(currValue >= 20 && currValue < 40) {
        //rafID = window.requestAnimationFrame(animateHandler);
        modOne();
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
    if (currValue < 20) {
        // decrement value
        currValue = currValue - speed;
    }
    if (currValue > 20) {
        currValue = 20;
    }
    if (currValue > 40) {
        currValue = 40;
    }
    if (currValue > 60) {
        currValue = 60;
    }
    if (currValue > 80) {
        currValue = 80;
    }
}


function modMax() {
    console.log("Most modified");
    modValue = 5;
}

function modOne() {
     console.log("Set to 1 mod ");
     modValue = 1;
}

// bind events
inputRange.addEventListener('mousedown', unlockStartHandler, false);
inputRange.addEventListener('mousestart', unlockStartHandler, false);
inputRange.addEventListener('mouseup', unlockEndHandler, false);
inputRange.addEventListener('touchend', unlockEndHandler, false);

// move gradient
inputRange.addEventListener('input', function() {
    //Change slide thumb color on way up
    if (this.value < 20) {
        console.log("0 mods");
    }
    if (this.value > 20 && this.value < 40) {
        console.log("1 mods");
    }
    if (this.value > 40 && this.value < 60) {
        console.log("2 mods");
    }
    if (this.value > 60 && this.value < 80) {
        console.log("3 mods");
    }
    if (this.value > 80 && this.value < 100) {
        console.log("4 mods");
    }
});

fetch('/search-result')
  .then(response => {
    return response.text();
  })
  .then(data => {
    console.log('Received message:', data);
  })
  .catch(error => {
    console.error('Fetch error from redirect:', error);
  });