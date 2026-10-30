# MelanoScan – AI Skin Cancer Detector

**A TechGurus Innovation · CAPACITI 2025**  
Tagline: *Early Detection. Equal Protection.*

Mobile-first Progressive Web App for AI-assisted skin lesion screening.

🌐 **Live demo (GitHub Pages):** https://mpumelelo10.github.io/MelanoScan/

---

## Quick start

### Option A – Static demo (no install)

1. Clone or download this repo.
2. Open `index.html` in Chrome or Edge.
3. Use the Scan screen for camera/gallery upload.

### Option B – Full app with secure Roboflow proxy (Python)

```bash
cd MelanoScan
python3 server.py
```

Then open: **http://localhost:8080**

The proxy keeps your Roboflow key on the server. Frontend only talks to `/api/analyze`.

### Option C – Node proxy

```bash
npm install express cors multer
node server.js
```

---

## Features

- Splash + strong medical disclaimer
- Home dashboard (Pink Ribbon Month, UV tip)
- Camera + gallery upload
- AI analysis via Roboflow (classification + detection) through secure proxy
- Results with confidence bar
- Education hub (types, ABCDE, prevention, skin of colour)
- Ask Melano chatbot
- Care tab with interactive Cape Town clinic map
- Bottom navigation, mobile-first, PWA-ready

## Important

This is a **screening prototype only**. It does **not** provide a medical diagnosis.

## Roboflow models

- Classification: `techguru-3vxeq/skin_lesion_classification-lyqqy`
- Detection: `techguru-3vxeq/skin-cancer-detection-3tjv9`

Set keys via environment variables:

```bash
export ROBOFLOW_PRIVATE_KEY="your_private_key"
export ROBOFLOW_PUBLIC_KEY="your_public_key"
python3 server.py
```

## Enable GitHub Pages

1. Go to repo **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / root
4. Save – site will be at https://mpumelelo10.github.io/MelanoScan/

---

© 2025 TechGurus · CAPACITI
