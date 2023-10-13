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
    window.location.href = "http://127.0.0.1:8000/views/search-result";
});


