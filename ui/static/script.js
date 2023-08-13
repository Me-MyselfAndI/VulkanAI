//Hide loader after page has loaded
function hideLoader() {
    document.getElementById('loader').style.visibility = 'hidden';
}
//Show loading animation after searching and while page is loading
showLoader = function(e) {
    e.preventDefault();
    document.getElementById('loader').style.visibility = 'show';
}

function goToSearch() {
    console.log('aint')
    fetch('/go-to').then(response => response.text()).then(url => {
        console.log('test')
        if (url) {
            window.location.href = url;  // Redirect the user to the specified URL
        } else {
            alert('Condition not met. No redirection.');  // Show an alert if condition is not met
        }
    })
    .catch(error => console.error('Error:', error));
}

