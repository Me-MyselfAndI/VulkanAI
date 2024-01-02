const express = import('express');
const fetch = import('node-fetch'); // npm install node-fetch

const app = express();

app.get('/fetchData', async (req, res) => {
  try {
    const url = req.query.url; // Get the URL parameter from the client

    const response = await fetch(url);
    const data = await response.text();

    res.send(data);
  } catch (error) {
    res.status(500).send({ error: 'Error fetching data' });
  }
});

const PORT = 3000; // Your desired port
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});