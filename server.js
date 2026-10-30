/**
 * MelanoScan Proxy Server
 * Keeps the private Roboflow API key off the frontend.
 */
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const https = require('https');

const ROBOFLOW_KEY = process.env.ROBOFLOW_PRIVATE_KEY || process.env.ROBOFLOW_PUBLIC_KEY || 'rf_1Bl00IYBBrOYOnh2k7snb9VOFoY2';
const CLASSIFICATION_MODEL = 'techguru-3vxeq/skin_lesion_classification-lyqqy';
const CLASSIFICATION_VERSION = '1';
const DETECTION_MODEL = 'techguru-3vxeq/skin-cancer-detection-3tjv9';
const DETECTION_VERSION = '1';

const app = express();
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 8 * 1024 * 1024 } });

app.use(cors());
app.use(express.static(path.join(__dirname)));

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', service: 'MelanoScan Proxy', models: { classification: CLASSIFICATION_MODEL, detection: DETECTION_MODEL } });
});

function postMultipart(hostname, urlPath, buffer, filename, mimetype) {
  return new Promise((resolve, reject) => {
    const boundary = '----MelanoScan' + Date.now();
    const preamble = Buffer.from(
      '--' + boundary + '\r\n' +
      'Content-Disposition: form-data; name="file"; filename="' + filename + '"\r\n' +
      'Content-Type: ' + (mimetype || 'image/jpeg') + '\r\n\r\n'
    );
    const epilogue = Buffer.from('\r\n--' + boundary + '--\r\n');
    const body = Buffer.concat([preamble, buffer, epilogue]);

    const options = {
      hostname: hostname,
      path: urlPath + '?api_key=' + ROBOFLOW_KEY,
      method: 'POST',
      headers: {
        'Content-Type': 'multipart/form-data; boundary=' + boundary,
        'Content-Length': body.length
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try { resolve(JSON.parse(data)); }
          catch (e) { reject(new Error('Invalid JSON')); }
        } else {
          reject(new Error('Roboflow ' + res.statusCode + ': ' + data.slice(0, 120)));
        }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

app.post('/api/analyze', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: 'No image file uploaded' });

    const buffer = req.file.buffer;
    const filename = req.file.originalname || 'lesion.jpg';
    const mimetype = req.file.mimetype || 'image/jpeg';

    let classData = null;
    let detectData = null;

    try {
      classData = await postMultipart(
        'classify.roboflow.com',
        '/' + CLASSIFICATION_MODEL + '/' + CLASSIFICATION_VERSION,
        buffer, filename, mimetype
      );
    } catch (e) {
      console.error('Classification failed:', e.message);
    }

    try {
      detectData = await postMultipart(
        'detect.roboflow.com',
        '/' + DETECTION_MODEL + '/' + DETECTION_VERSION,
        buffer, filename, mimetype
      );
    } catch (e) {
      console.warn('Detection skipped:', e.message);
    }

    if (!classData) {
      return res.status(502).json({ error: 'Roboflow classification failed', fallback: true });
    }

    res.json({ classification: classData, detection: detectData, source: 'roboflow-proxy' });
  } catch (err) {
    console.error('Proxy error:', err);
    res.status(500).json({ error: err.message || 'Internal proxy error' });
  }
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, '0.0.0.0', () => {
  console.log('MelanoScan running at http://localhost:' + PORT);
  console.log('Proxy: POST /api/analyze');
});
