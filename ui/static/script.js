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
    event.preventDefault();
    //showLoader(event);
    let inputValue = document.getElementById("search")[0].value;
    console.log(inputValue);
    let $;
    $.ajax = function (param) {

    }
    //window.location.href = "http://127.0.0.1:8000/views/search-result";
    $.ajax({
      type: "POST",
      url: "..\views.py",
      data: { param: text}
    }).done(function() {

    });
});


