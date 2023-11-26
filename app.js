const express = require('express');
const { spawn } = require('child_process');
const app = express();
var cors = require("cors");
app.use(express.json());
app.use(cors())
app.get("/", (req, res) => {
  res.send("movie recomendation 2");
});
app.post('/recommend', async (req, res) => {
  console.log("got api call", req.body.movie)
  const pythonProcess = spawn('python', ['final.py', req.body.movie]);
  let output = '';
  pythonProcess.stdout.on('data', (data) => {
    output += data.toString();
  });
console.log(output, "output")
  pythonProcess.on('close', (code) => {
    if (code === 0) {
      res.json({ recommendations: JSON.parse(output) });
    } else {
      res.status(500).send('Error executing Python script');
    }
  });
});

app.listen(5000, () => console.log('Server listening on port 3000'));
