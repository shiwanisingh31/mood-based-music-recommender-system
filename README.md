# 🎵 Mood Music Recommender

A full-stack web application that recommends music based on your current mood — 
detected automatically via webcam using AI, or entered manually.

## ✨ Features

- 🎭 **Emotion Detection** — Uses DeepFace AI to detect your mood via webcam
- 😊 **Mood-Based Recommendations** — Get songs for Happy, Sad, Angry, or Neutral moods
- 😌 **Neutral Mood A–Z Catalog** — Browse and play a full song catalog alphabetically
- 🔐 **User Authentication** — Register, login, logout with secure password hashing
- ❤️ **Liked Songs** — Save your favourite songs
- 📁 **Upload Your Own Music** — Upload MP3/WAV files to your personal library
- 🔀 **Shuffle Play** — Shuffle your entire music library
- 📋 **Playlists** — Create and manage custom playlists
- 🔥 **Trending Artists** — Discover trending artists

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Database | SQLite (dev), PostgreSQL (prod) |
| Auth | Flask-Login, Werkzeug |
| AI/ML | DeepFace, OpenCV |
| Frontend | HTML, CSS, JavaScript |
| Deployment | Render |

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository
   git clone https://github.com/YOUR_USERNAME/mood-music.git
   cd mood-music

2. Install dependencies
   pip install -r requirements.txt

3. Run the app
   python app.py

4. Open your browser
   http://127.0.0.1:5000

## 📁 Project Structure

mood-music/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── render.yaml             # Render deployment config
├── TEMPLATES/              # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── neutral_songs.html
│   ├── login.html
│   └── register.html
├── STATIC/                 # CSS, JS assets
├── default_songs/          # Pre-loaded songs
└── music_uploads/          # User uploaded songs

## 🌐 Live Demo
https://your-app-name.onrender.com

## 👩‍💻 Author
Made with ❤️ by YOUR_NAME
