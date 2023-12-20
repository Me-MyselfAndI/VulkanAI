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

function hideLoaderDemo() {
    wait(3000);//Wait a little before rendering page
    hideLoader();
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
    console.log("Sending user to new page");
    window.location.href = "http://127.0.0.1:8000/views/search-result";
    // Check response is ready or not
    if (xhr.readyState == 4 && xhr.status == 201) {
        console.log("Received data");
        console.log(xhr.responseText);

    }
}

document.getElementById("search-button").addEventListener("click", function(event) {
    xhr = null;
    event.preventDefault();

    let prefWebsite = document.getElementById("website-value").value;//Get prefered website for searching
    let inputValue = document.getElementById("search-input").value;//If using input field use 'document.getElementById("search-input")[0].value'
    console.log(inputValue);
    console.log(prefWebsite)

    xhr = getXmlHttpRequestObject();
    xhr.onreadystatechange = sendToNewPage;
    xhr.open("POST", "http://127.0.0.1:8000/views/search-result", true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    // Send the request over the network
    xhr.send(JSON.stringify({"data": inputValue, "pref-website": prefWebsite}));
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
       if(e.which == 13) e.preventDefault();
    },
    keydown: function (e) {
        var text = $(this).val();
        //Decrease size of search bar as text gets deleted
        if(e.which === 8 && text.length % 50 === 0 && text.length > 30) $(this).css('height', '-=' + 20 + 'px');
    }
});

//Receive notification that data is loaded and ready to be displayed
/*fetch('/search-result', {
    method: 'POST',
})
    .then(response => {
        if(response.status === 201) {
            console.log("Message received succesfully");
        } else {
            console.error("Unexpected status code: ", response.status);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    })

/*fetch('/search-result')
  .then(response => {
    return response.text();
  })
  .then(data => {
    console.log('Received message:', data);
  })
  .catch(error => {
    console.error('Fetch error:', error);
  });*/


