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

//Refactor and render links
$(document).on('click', '.result-link', function( event ) {
   //alert( $(this).attr('class') )
    console.log("Clicked link");
   let clickedLink = $(this).attr('class').href;
   console.log($(this));
});
