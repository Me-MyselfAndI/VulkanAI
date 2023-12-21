fetch('/search-result')
  .then(response => {
    return response.text();
  })
  .then(data => {
    console.log('Received message:', data);
  })
  .catch(error => {
    console.error('Fetch error from loader:', error);
  });