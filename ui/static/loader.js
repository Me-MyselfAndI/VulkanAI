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
