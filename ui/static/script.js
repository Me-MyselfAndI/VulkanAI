//Request to call python functions
let xhr = null;
getXmlHttpRequestObject = function () {
    if (!xhr) {
        // Create a new XMLHttpRequest object
        xhr = new XMLHttpRequest();
    }
    return xhr;
};

let searchType = "basic";

//Hide loader after page has loaded
function hideLoader() {
    document.getElementById('loader').style.visibility = 'hidden';
}
//Show loading animation after searching and while page is loading
showLoader = function(e) {
    console.log("show loader");
    document.getElementById('loader').style.visibility = 'visible';
}

//Non Production Kostyl
function wait(ms){
   var start = new Date().getTime();
   var end = start;
   while(end < start + ms) {
     end = new Date().getTime();
  }
}

//Move user search result page
function sendToNewPage() {
    console.log("Sent user to new page");
    showLoader()

    // Check response is ready or not
    if (xhr.readyState === 4 || xhr.status === 201) {
        if(searchType == "basic"){
            //window.location.href = "https://result.vulkanai.org/views/search-result"; //Server Side
            window.location.href = "http://127.0.0.1:8000/views/search-result"; //Local Side
        } else {
            //window.location.href = "https://result.vulkanai.org/views/final-result"; //Server Side
            window.location.href = "http://127.0.0.1:8000/views/final-result"; //Local Side
        }
        console.log("received data");
        console.log(xhr.responseText);
    }
}

//Send data to Python
document.getElementById("search-button").addEventListener("click", function(event) {
    xhr = null;
    let prefWebsite = document.getElementById("website-value").value;//Get prefered website for searching
    let inputValue = document.getElementById("search-input").value;//If using input field use 'document.getElementById("search-input")[0].value'
    console.log(inputValue);
    console.log(prefWebsite)
    console.log(searchType)

    xhr = getXmlHttpRequestObject();
    xhr.onreadystatechange = sendToNewPage;

    //SEND REQUEST
    //xhr.open("POST", "https://result.vulkanai.org/views/search-result", true); //Server Side
    xhr.open("POST", "http://127.0.0.1:8000/views/search-result", true); //Local Side

    xhr.setRequestHeader("Accept", "application/json");
    xhr.setRequestHeader("Content-Type", "application/json");//application/json;charset=UTF-8

    xhr.mode = 'no-cors';
    // Send the request over the network
    xhr.send(JSON.stringify({"data": inputValue, "pref-website": prefWebsite, "search-type": searchType}));
});

//Make search bar grow in height as user keeps typing into it
var span = $('<span>').css('display','inline-block')
                      .css('word-break','break-all')
                      .appendTo('body').css('visibility','hidden');
function initSpan(textarea){
  span.text(textarea.text())
      .width("0")
      .css('font',textarea.css('font'));
}

$('textarea').on({
    input: function(){
       var text = $(this).val();
       span.text(text);
       //Extend search bar as user keeps typing
       if(text.length % 50 === 0) $(this).height('1.2em');
       //Make search bar small if there is nothing in it
       if(text.length === 0) $(this).height('40px');
    },
    focus: function(){
       initSpan($(this));
    },
    keypress: function(e){
       //cancel the Enter keystroke, otherwise a new line will be created
       //if(e.which == 13) e.preventDefault();
    },
    keydown: function (e) {
        var text = $(this).val();
        //Decrease size of search bar as text gets deleted
        if(e.which === 8 && text.length % 50 === 0 && text.length > 30) $(this).css('height', '-=' + 20 + 'px');
    }
});

//Send what type of search user is using
document.getElementById("speed").addEventListener("click", function(event) {
    let checkmark = document.getElementById("speed"); // Declare checkmark locally
    if(checkmark.checked) {
        searchType = "speed"; // Assign new value to the globally declared searchType
    } else {
        searchType = "basic"; // Assign new value to the globally declared searchType
    }
    console.log(searchType);
});
