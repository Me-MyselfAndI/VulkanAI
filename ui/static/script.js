//Request to call python functions
let xhr = null;
getXmlHttpRequestObject = function () {
    if (!xhr) {
        // Create a new XMLHttpRequest object
        xhr = new XMLHttpRequest();
    }
    return xhr;
};
//Hide loader after page has loaded
function hideLoader() {
    document.getElementById('loader').style.visibility = 'hidden';
}
//Show loading animation after searching and while page is loading
showLoader = function(e) {
    e.preventDefault();
    document.getElementById('loader').style.visibility = 'show';
}

//Move user search result page
function sendToNewPage() {
    // Check response is ready or not
    if (xhr.readyState == 4 && xhr.status == 201) {
        console.log("Sending user to new page");
        window.location.href = "http://127.0.0.1:8000/views/search-result";
    }
}

document.getElementById("search").addEventListener("submit", function(event) {
    xhr = null;
    event.preventDefault();

    let inputValue = document.getElementById("search")[0].value;
    console.log(inputValue);

    xhr = getXmlHttpRequestObject();
    xhr.open("POST", "http://127.0.0.1:8000/views/search-result", true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    // Send the request over the network
    xhr.send(JSON.stringify({"data": inputValue}));
    xhr.onreadystatechange = sendToNewPage();
});

//Make search bar grow in height as user keeps typing into it
var span = $('<span>').css('display','inline-block')
                      .css('word-break','break-all')
                      .appendTo('body').css('visibility','hidden');
function initSpan(textarea){
  span.text(textarea.text())
      .width(textarea.width())
      .css('font',textarea.css('font'));
}
/*
$('textarea').on({
    input: function(){
       var text = $(this).val();
       span.text(text);
       $(this).height(text ? span.height() : '1.1em');
    },
    focus: function(){
       initSpan($(this));
    },
    keypress: function(e){
       //cancel the Enter keystroke, otherwise a new line will be created
       if(e.which == 13) e.preventDefault();
    }
});
 */
