function wait(ms){
   var start = new Date().getTime();
   var end = start;
   while(end < start + ms) {
     end = new Date().getTime();
  }
}


fetch('/search-result', {
    method: 'POST',
})
    .then(response => {
        if(response.status === 201 || response.status === 200) {
            window.location.href = "http://127.0.0.1:8000/views/go-to";
        } else {
            console.error("Unexpected status code from loader: ", response.status);
        }

    })
    .catch(error => {
        console.error('Error:', error);
    })

document.addEventListener('DOMContentLoaded', function() {
            var dataToSend = {
                key: 'value', // Your data to send
                anotherKey: 'anotherValue'
            };

            // Make an AJAX POST request
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/search_result', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === XMLHttpRequest.DONE) {
                    if (xhr.status === 200) {
                        var response = JSON.parse(xhr.responseText);
                        console.log('Response from server:', response);
                    } else {
                        console.error('Error:', xhr.status);
                    }
                }
            };
            xhr.send(JSON.stringify(dataToSend));
        });