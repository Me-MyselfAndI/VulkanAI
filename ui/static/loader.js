fetch('/search-result', {
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