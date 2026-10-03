<div align="center">
  
# 🤖 AI Face Greeting & Access Control

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/OpenCV-27338e?style=for-the-badge&logo=OpenCV&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" />
</p>

An intelligent facial recognition system that detects, verifies, and warmly greets users with personalized audio! Features a sleek, responsive UI, remote camera processing, and a full-featured Admin Dashboard for identity management.

</div>

---

## ✨ Features

- **Live Facial Recognition:** Real-time face detection and identification using OpenCV's robust LBPH algorithm.
- **Liveness Detection:** Integrated blink detection ensures that the user is a real human, preventing spoofing via photos or phones.
- **Personalized Audio Greetings:** Automatically generates AI voice greetings (via Google TTS) when a user is recognized, or allows for custom audio uploads (MP3, WAV, etc.).
- **Powerful Admin Dashboard:**
  - Enroll new users effortlessly via live camera or direct photo upload.
  - Assign and manage custom audio greetings for any enrolled identity.
  - View auto-recorded short video logs (GIFs) of recent scan activity.
  - Check real-time analytics (Total Enrolled, Scans Today, Storage Used).
- **Headless-Ready Architecture:** Designed for production. Video streams and audio playbacks are handled completely client-side in the browser, meaning the backend can be hosted safely on a headless cloud server (AWS, GCP, etc.) without crashing over local hardware APIs.

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Waitress (Production WSGI)
- **Computer Vision:** OpenCV (Haar Cascades, LBPH Recognizer, Image processing)
- **Audio:** gTTS (Google Text-to-Speech)
- **Frontend:** HTML5, CSS3 (Modern Glassmorphism UI), Vanilla JavaScript

---

## 🚀 Quick Start

### 1. Prerequisites
Make sure you have Python installed on your machine.

### 2. Installation
Clone the repository and install the required dependencies:

```bash
git clone https://github.com/YOUR_USERNAME/ai-face-greeting.git
cd ai-face-greeting

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Server
Start the production-ready server:

```bash
python server.py
```

### 4. Access the App
- **Live Scanner:** Open your browser and navigate to `http://127.0.0.1:5000`
- **Admin Dashboard:** Click "⚙ Admin Dashboard" in the top right or go directly to `http://127.0.0.1:5000/dashboard`

---

## 📸 How to Use

1. **Enroll a Face:** Go to the Admin Dashboard. Enter a name and click **"Live Enroll"** (which redirects you to the camera to scan your face), or click **"Upload Photo"** to enroll instantly via an image file.
2. **Scan:** Stand in front of the camera on the main scanner page. The system will detect your face, verify liveness, and verify your identity!
3. **Custom Audio:** Go to the Admin Dashboard and click **"🎵 Change Audio"** under any enrolled person's card to upload a custom greeting track!

---

## 🔒 Security Note
By default, the Admin Dashboard is protected by a lightweight client-side lock. For a fully exposed public deployment, it is highly recommended to wrap the dashboard endpoints with standard server-side authentication (e.g., Flask-Login or JWTs).

<br>
<div align="center">
  Made with ❤️ by Vishal
</div>
