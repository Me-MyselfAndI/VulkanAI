function hideLoader() {
    document.getElementById('loader').style.visibility = 'hidden';
}

showLoader = function(e) {
    e.preventDefault();
    document.getElementById('loader').style.visibility = 'show';
}

$(document).keypress(function(e) {
    if (e.which == 13) {
        $('#loader').hide();
    }
});