from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import random
import threading
from sqlalchemy import inspect, text


def _get_folder(name_options):
    base = os.path.dirname(os.path.abspath(__file__))
    for name in name_options:
        path = os.path.join(base, name)
        if os.path.isdir(path):
            return path
    return os.path.join(base, name_options[0])


app = Flask(
    __name__,
    template_folder=_get_folder(["TEMPLATES", "templates"]),
    static_folder=_get_folder(["STATIC", "static"]),
    static_url_path="/static",
)

# ==================== CONFIGURATION ====================
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///mood_music.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music_uploads")
ALLOWED_EXTENSIONS = {"mp3", "wav", "ogg", "m4a", "flac"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max per file

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DEFAULT_SONGS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "default_songs")
os.makedirs(DEFAULT_SONGS_FOLDER, exist_ok=True)

DEFAULT_SONGS = [
    {"filename": "1_1772524189_ZHU_-_In_the_Morning_mp3.pm.mp3", "title": "ZHU In The Morning"},
    {"filename": "1_1772524566_Kishore_Kumar_Lata_Mangeshkar_-_Oh_Saathi_Re_mp3.pm.mp3", "title": "Kishore Kumar Oh Saathi Re"},
    {"filename": "1_1772524580_Imagine_Dragons_-_Radioactive_Piano_mp3.pm.mp3", "title": "Imagine Dragons Radioactive"},
    {"filename": "neutral_Gehra_Hua.mp3", "title": "Gehra Hua — Irshad Kamil"},
    {"filename": "neutral_I_Really_Do.mp3", "title": "I Really Do — Karan Aujla"},
    {"filename": "neutral_Pal_Pal.mp3", "title": "Pal Pal — Afusic"},
    {"filename": "neutral_new_1.mp3", "title": "Let Me Down Slowly — Alec Benjamin"},
    {"filename": "neutral_new_2.mp3", "title": "Chhalakata Hamro Jawaniya — Priyanka Singh"},
    {"filename": "neutral_new_3.mp3", "title": "Phurr — Yo Yo Honey Singh"},
    {"filename": "neutral_new_4.mp3", "title": "Mitha Bolke — Nirvair Pannu"},
    {"filename": "neutral_new_5.mp3", "title": "Haseen — Talwiinder"},
    {"filename": "neutral_new_6.mp3", "title": "Saiyaara — Faheem Abdullah"},
    {"filename": "neutral_new_7.mp3", "title": "Barbaad — The Rish"},
    {"filename": "neutral_new_8.mp3", "title": "Payal — Yo Yo Honey Singh"},
    {"filename": "neutral_new_9.mp3", "title": "Saara India — Payal Dev"},
    {"filename": "neutral_new_10.mp3", "title": "Raanjhan — Sachet Parampara"},
    {"filename": "neutral_new_11.mp3", "title": "Zaalim — Badshah"},
    {"filename": "neutral_new_12.mp3", "title": "Tera Ban Jaunga — Dj Yogi"},
    {"filename": "neutral_new_13.mp3", "title": "Paint The Town Red — Doja Cat"},
    {"filename": "neutral_new_14.mp3", "title": "EMPIRE — Ogryzek"},
    {"filename": "neutral_new_15.mp3", "title": "Bahon Mein Chale Aao"},
    {"filename": "neutral_new_16.mp3", "title": "Agar Tum Saath Ho — Tamasha"},
    {"filename": "neutral_new_17.mp3", "title": "Ab Mujhe Raat Din"},
]

NEUTRAL_DEFAULT_FILENAMES = {
    "neutral_Gehra_Hua.mp3",
    "neutral_I_Really_Do.mp3",
    "neutral_Pal_Pal.mp3",
    "neutral_new_1.mp3",
    "neutral_new_2.mp3",
    "neutral_new_3.mp3",
    "neutral_new_4.mp3",
    "neutral_new_5.mp3",
    "neutral_new_6.mp3",
    "neutral_new_7.mp3",
    "neutral_new_8.mp3",
    "neutral_new_9.mp3",
    "neutral_new_10.mp3",
    "neutral_new_11.mp3",
    "neutral_new_12.mp3",
    "neutral_new_13.mp3",
    "neutral_new_14.mp3",
    "neutral_new_15.mp3",
    "neutral_new_16.mp3",
    "neutral_new_17.mp3",
}

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    songs = db.relationship("Song", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_default = db.Column(db.Boolean, default=False)
    liked = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "uploaded_at": self.uploaded_at.strftime("%d %b %Y"),
            "liked": bool(self.liked),
        }


playlist_songs = db.Table(
    "playlist_songs",
    db.Column("playlist_id", db.Integer, db.ForeignKey("playlist.id")),
    db.Column("song_id", db.Integer, db.ForeignKey("song.id")),
)


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    songs = db.relationship("Song", secondary=playlist_songs, lazy="subquery")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.strftime("%d %b %Y"),
            "song_count": len(self.songs),
        }


def seed_default_songs(user_id):
    for song_info in DEFAULT_SONGS:
        filepath = os.path.join(DEFAULT_SONGS_FOLDER, song_info["filename"])
        if not os.path.exists(filepath):
            continue
        already_exists = Song.query.filter_by(
            user_id=user_id, filename=song_info["filename"]
        ).first()
        if not already_exists:
            song = Song(
                title=song_info["title"],
                filename=song_info["filename"],
                user_id=user_id,
                is_default=True,
            )
            db.session.add(song)
    db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("All fields are required!", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters long!", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "error")
            return redirect(url_for("register"))

        new_user = User(username=username, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            seed_default_songs(new_user.id)
            return redirect(url_for("login"))
        except Exception:
            db.session.rollback()
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") in ("1", "true", "on", "yes")

        if not username or not password:
            flash("Please enter both username and password!", "error")
            return redirect(url_for("login"))

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.username}! 🎵", "success")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("dashboard"))

        flash("Invalid username or password!", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f"Goodbye, {username}! See you soon! 👋", "info")
    return redirect(url_for("login"))


@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/dashboard")
@login_required
def dashboard():
    seed_default_songs(current_user.id)
    return render_template("dashboard.html")


@app.route("/music/upload", methods=["POST"])
@login_required
def upload_song():
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")
    uploaded = []

    for file in files:
        if file.filename == "":
            continue
        if not allowed_file(file.filename):
            continue

        original_name = secure_filename(file.filename)
        unique_name = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{original_name}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(save_path)

        title = os.path.splitext(file.filename)[0].replace("_", " ").replace("-", " ")

        song = Song(title=title, filename=unique_name, user_id=current_user.id)
        db.session.add(song)
        db.session.flush()
        uploaded.append(song.to_dict())

    db.session.commit()
    return jsonify({"success": True, "songs": uploaded})


@app.route("/music/songs")
@login_required
def get_songs():
    songs = Song.query.filter_by(user_id=current_user.id).order_by(Song.uploaded_at.desc()).all()
    return jsonify({"songs": [s.to_dict() for s in songs]})


@app.route("/music/shuffle")
@login_required
def shuffle_songs():
    songs = Song.query.filter_by(user_id=current_user.id).all()
    random.shuffle(songs)
    return jsonify({"songs": [s.to_dict() for s in songs]})


@app.route("/music/play/<int:song_id>")
@login_required
def play_song(song_id):
    song = Song.query.filter_by(id=song_id, user_id=current_user.id).first_or_404()
    if song.is_default:
        return send_from_directory(DEFAULT_SONGS_FOLDER, song.filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], song.filename)


@app.route("/music/delete/<int:song_id>", methods=["DELETE"])
@login_required
def delete_song(song_id):
    song = Song.query.filter_by(id=song_id, user_id=current_user.id).first_or_404()

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], song.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(song)
    db.session.commit()
    return jsonify({"success": True, "message": f'"{song.title}" deleted.'})


@app.route("/music/like/<int:song_id>", methods=["POST"])
@login_required
def toggle_like_song(song_id):
    song = Song.query.filter_by(id=song_id, user_id=current_user.id).first_or_404()
    song.liked = not bool(song.liked)
    db.session.commit()
    return jsonify(
        {
            "success": True,
            "liked": bool(song.liked),
            "message": (
                f'❤️ "{song.title}" added to Liked Songs'
                if song.liked
                else f'🤍 "{song.title}" removed from Liked Songs'
            ),
        }
    )


@app.route("/music/liked")
@login_required
def get_liked_songs():
    songs = (
        Song.query.filter_by(user_id=current_user.id, liked=True)
        .order_by(Song.uploaded_at.desc())
        .all()
    )
    return jsonify({"songs": [s.to_dict() for s in songs]})


@app.route("/liked-songs")
@login_required
def liked_songs_page():
    return render_template("liked_songs.html")


@app.route("/neutral-songs")
@login_required
def neutral_songs_page():
    seed_default_songs(current_user.id)
    return render_template("neutral_songs.html")


@app.route("/api/neutral-songs")
@login_required
def api_neutral_songs():
    seed_default_songs(current_user.id)
    songs = (
        Song.query.filter(
            Song.user_id == current_user.id,
            Song.filename.in_(list(NEUTRAL_DEFAULT_FILENAMES)),
        )
        .order_by(Song.title.asc())
        .all()
    )

    def split_artist(title: str):
        if "—" in title:
            parts = [p.strip() for p in title.split("—", 1)]
            if len(parts) == 2:
                return parts[0], parts[1]
        if "-" in title:
            parts = [p.strip() for p in title.split("-", 1)]
            if len(parts) == 2:
                return parts[0], parts[1]
        return title, "Neutral Picks"

    out = []
    for s in songs:
        t, artist = split_artist(s.title)
        path = (
            os.path.join(DEFAULT_SONGS_FOLDER, s.filename)
            if s.is_default
            else os.path.join(app.config["UPLOAD_FOLDER"], s.filename)
        )
        out.append(
            {
                "song_id": s.id,
                "title": t,
                "artist": artist,
                "playable": os.path.exists(path),
            }
        )
    return jsonify({"songs": out})


@app.route("/recommend", methods=["POST"])
def recommend():
    mood = request.form["mood"].lower()

    if mood == "happy":
        songs = [
            "Happy - Pharrell Williams",
            "Good Vibrations - The Beach Boys",
            "Don't Stop Me Now - Queen",
            "Walking on Sunshine - Katrina",
            "I Gotta Feeling - Black Eyed Peas",
        ]
    elif mood == "sad":
        songs = [
            "Someone Like You - Adele",
            "Hurt - Johnny Cash",
            "The Night We Met - Lord Huron",
            "Fix You - Coldplay",
            "Let Her Go - Passenger",
        ]
    elif mood == "angry":
        songs = [
            "Break Stuff - Limp Bizkit",
            "Killing in the Name - RATM",
            "Enter Sandman - Metallica",
            "Bodies - Drowning Pool",
            "Smells Like Teen Spirit - Nirvana",
        ]
    elif mood == "neutral":
        songs = [s["title"] for s in DEFAULT_SONGS if s["filename"] in NEUTRAL_DEFAULT_FILENAMES]
    else:
        songs = ["Please enter: happy, sad, or angry"]

    return render_template("results.html", mood=mood, songs=songs)


def _preload_deepface():
    try:
        print("[DeepFace] Loading AI models (first time may take 2-5 min)...")
        import numpy as np
        import cv2
        from deepface import DeepFace

        img = np.zeros((48, 48, 3), dtype=np.uint8)
        temp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_warmup.jpg")
        cv2.imwrite(temp, img)
        try:
            DeepFace.analyze(
                img_path=temp, actions=["emotion"], enforce_detection=False, silent=True
            )
        except TypeError:
            DeepFace.analyze(img_path=temp, actions=["emotion"], enforce_detection=False)
        if os.path.exists(temp):
            os.remove(temp)
        print("[DeepFace] Models ready!")
    except Exception as e:
        print(f"[DeepFace] Pre-load warning: {e} (will load on first use)")


@app.route("/detect-emotion", methods=["POST"])
def detect_emotion():
    import base64
    import numpy as np
    import cv2

    try:
        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "No image data received"}), 400

        image_data = data["image"]
        if "," in image_data:
            image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)

        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({"error": "Invalid image - could not decode"}), 400

        temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_face.jpg")
        cv2.imwrite(temp_path, img)

        try:
            from deepface import DeepFace

            try:
                result = DeepFace.analyze(
                    img_path=temp_path,
                    actions=["emotion"],
                    enforce_detection=False,
                    silent=True,
                )
            except TypeError:
                result = DeepFace.analyze(
                    img_path=temp_path, actions=["emotion"], enforce_detection=False
                )
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

        if isinstance(result, list):
            first = result[0] if result else {}
        else:
            first = result

        emotion = first.get("dominant_emotion", "neutral") or "neutral"

        emotion_to_mood = {
            "happy": "happy",
            "neutral": "neutral",
            "surprise": "happy",
            "sad": "sad",
            "fear": "sad",
            "angry": "angry",
            "disgust": "angry",
        }

        mood = emotion_to_mood.get(emotion, "happy")

        if mood == "happy":
            songs = [
                "Happy - Pharrell Williams",
                "Good Vibrations - The Beach Boys",
                "Don't Stop Me Now - Queen",
                "Walking on Sunshine - Katrina",
                "I Gotta Feeling - Black Eyed Peas",
            ]
        elif mood == "neutral":
            songs = [s["title"] for s in DEFAULT_SONGS if s["filename"] in NEUTRAL_DEFAULT_FILENAMES]
        elif mood == "sad":
            songs = [
                "Someone Like You - Adele",
                "Hurt - Johnny Cash",
                "The Night We Met - Lord Huron",
                "Fix You - Coldplay",
                "Let Her Go - Passenger",
            ]
        else:
            songs = [
                "Break Stuff - Limp Bizkit",
                "Killing in the Name - RATM",
                "Enter Sandman - Metallica",
                "Bodies - Drowning Pool",
                "Smells Like Teen Spirit - Nirvana",
            ]

        return jsonify({"emotion": emotion, "mood": mood, "songs": songs})

    except Exception as e:
        print(f"Error in emotion detection: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/playlist/create", methods=["POST"])
@login_required
def create_playlist():
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Playlist name is required"}), 400
    playlist = Playlist(name=name, user_id=current_user.id)
    db.session.add(playlist)
    db.session.commit()
    return jsonify({"success": True, "playlist": playlist.to_dict()})


@app.route("/playlist/all")
@login_required
def get_playlists():
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    return jsonify({"playlists": [p.to_dict() for p in playlists]})


@app.route("/playlist/<int:playlist_id>/add-song", methods=["POST"])
@login_required
def add_song_to_playlist(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    song_id = data.get("song_id")
    song = Song.query.filter_by(id=song_id, user_id=current_user.id).first_or_404()
    if song not in playlist.songs:
        playlist.songs.append(song)
        db.session.commit()
    return jsonify({"success": True, "message": f'"{song.title}" added to {playlist.name}'})


@app.route("/playlist/<int:playlist_id>/remove-song", methods=["POST"])
@login_required
def remove_song_from_playlist(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    song_id = data.get("song_id")
    song = Song.query.filter_by(id=song_id, user_id=current_user.id).first_or_404()
    if song in playlist.songs:
        playlist.songs.remove(song)
        db.session.commit()
    return jsonify({"success": True, "message": f'"{song.title}" removed from {playlist.name}'})


@app.route("/playlist/<int:playlist_id>/songs")
@login_required
def get_playlist_songs(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first_or_404()
    return jsonify({"playlist": playlist.name, "songs": [s.to_dict() for s in playlist.songs]})


@app.route("/playlist/<int:playlist_id>/delete", methods=["DELETE"])
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first_or_404()
    db.session.delete(playlist)
    db.session.commit()
    return jsonify({"success": True, "message": f'"{playlist.name}" deleted.'})


@app.route("/trending")
@login_required
def trending_page():
    return render_template("trending.html")


@app.route("/api/trending-artists")
def get_trending_artists():
    try:
        trending_artists = [
            {
                "id": "1",
                "name": "Taylor Swift",
                "image": "https://i.scdn.co/image/ab6761610000e5ebe672b5f553298dcdccb0e676",
                "genres": ["pop", "country"],
                "popularity": 100,
                "followers": 95000000,
                "spotify_url": "https://open.spotify.com/artist/06HL4z0CvFAxyc27GXpf02",
            },
            {
                "id": "2",
                "name": "Bad Bunny",
                "image": "https://i.scdn.co/image/ab6761610000e5eb19c2790744c792d05570bb71",
                "genres": ["latin", "reggaeton"],
                "popularity": 99,
                "followers": 72000000,
                "spotify_url": "https://open.spotify.com/artist/4q3ewBCX7sLwd24euuV69X",
            },
            {
                "id": "3",
                "name": "The Weeknd",
                "image": "https://i.scdn.co/image/ab6761610000e5eb214f3cf1cbe7139c1e26ffbb",
                "genres": ["r&b", "pop"],
                "popularity": 98,
                "followers": 68000000,
                "spotify_url": "https://open.spotify.com/artist/1Xyo4u8uXC1ZmMpatF05PJ",
            },
        ]

        return jsonify({"success": True, "artists": trending_artists})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/artist/<artist_id>/top-tracks")
def get_artist_top_tracks(artist_id):
    try:
        tracks = [
            {
                "id": "1",
                "name": "Popular Hit #1",
                "album": "Latest Album",
                "album_image": "https://via.placeholder.com/300",
                "preview_url": None,
                "duration_ms": 210000,
                "spotify_url": "https://open.spotify.com",
            },
            {
                "id": "2",
                "name": "Popular Hit #2",
                "album": "Greatest Hits",
                "album_image": "https://via.placeholder.com/300",
                "preview_url": None,
                "duration_ms": 195000,
                "spotify_url": "https://open.spotify.com",
            },
        ]

        return jsonify({"success": True, "tracks": tracks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def init_db():
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        song_columns = {col["name"] for col in inspector.get_columns("song")}
        if "liked" not in song_columns:
            db.session.execute(text("ALTER TABLE song ADD COLUMN liked BOOLEAN DEFAULT 0"))
            db.session.commit()
        print("Database initialized successfully!")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("MOOD MUSIC RECOMMENDER + AUTH")
    print("=" * 50)
    init_db()
    threading.Thread(target=_preload_deepface, daemon=True).start()
    app.run(debug=True)
