from flask import Flask, render_template, request, jsonify
import os
import threading

# Ensure Flask finds templates and static (handles TEMPLATES/STATIC vs lowercase)
def _get_folder(name_options):
    base = os.path.dirname(os.path.abspath(__file__))
    for name in name_options:
        path = os.path.join(base, name)
        if os.path.isdir(path):
            return path
    return os.path.join(base, name_options[0])

app = Flask(
    __name__,
    template_folder=_get_folder(['TEMPLATES', 'templates']),
    static_folder=_get_folder(['STATIC', 'static']),
    static_url_path='/static'
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    mood = request.form['mood'].lower()
    
    if mood == "happy":
        songs = [
            "Happy - Pharrell Williams",
            "Good Vibrations - The Beach Boys",
            "Don't Stop Me Now - Queen",
            "Walking on Sunshine - Katrina",
            "I Gotta Feeling - Black Eyed Peas"
        ]
    elif mood == "sad":
        songs = [
            "Someone Like You - Adele",
            "Hurt - Johnny Cash",
            "The Night We Met - Lord Huron",
            "Fix You - Coldplay",
            "Let Her Go - Passenger"
        ]
    elif mood == "angry":
        songs = [
            "Break Stuff - Limp Bizkit",
            "Killing in the Name - RATM",
            "Enter Sandman - Metallica",
            "Bodies - Drowning Pool",
            "Smells Like Teen Spirit - Nirvana"
        ]
    else:
        songs = ["Please enter: happy, sad, or angry"]
    
    return render_template('results.html', mood=mood, songs=songs)

def _preload_deepface():
    """Pre-load DeepFace models on startup so first emotion detection is fast."""
    try:
        print("[DeepFace] Loading AI models (first time may take 2-5 min)...")
        import numpy as np
        import cv2
        from deepface import DeepFace
        # Create tiny test image to trigger model load
        img = np.zeros((48, 48, 3), dtype=np.uint8)
        temp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_warmup.jpg')
        cv2.imwrite(temp, img)
        DeepFace.analyze(img_path=temp, actions=['emotion'], enforce_detection=False, silent=True)
        if os.path.exists(temp):
            os.remove(temp)
        print("[DeepFace] ✓ Models ready! Emotion detection will be fast now.")
    except Exception as e:
        print(f"[DeepFace] Pre-load warning: {e} (will load on first use)")

@app.route('/detect-emotion', methods=['POST'])
def detect_emotion():
    import base64
    import os
    import numpy as np
    
    try:
        print("[Emotion] Request received...")
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data received'}), 400
        
        print("[Emotion] Decoding image...")
        image_data = data['image']
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        import cv2
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'error': 'Invalid image - could not decode'}), 400
        
        temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)) or '.', 'temp_face.jpg')
        cv2.imwrite(temp_path, img)
        
        try:
            print("[Emotion] Running AI analysis (this may take 30-60 sec on first use)...")
            from deepface import DeepFace
            try:
                result = DeepFace.analyze(img_path=temp_path, actions=['emotion'], enforce_detection=False, silent=True)
            except TypeError:
                result = DeepFace.analyze(img_path=temp_path, actions=['emotion'], enforce_detection=False)
            print("[Emotion] ✓ Analysis complete!")
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
        
        # Handle both list and dict return formats (DeepFace API varies by version)
        if isinstance(result, list):
            first = result[0] if result else {}
        else:
            first = result
            
        emotion = first.get('dominant_emotion', 'neutral')
        if not emotion and isinstance(result, list) and result:
            emotion = result[0].get('dominant_emotion', 'neutral')
        
        emotion_to_mood = {
            'happy': 'happy',
            'neutral': 'happy',
            'surprise': 'happy',
            'sad': 'sad',
            'fear': 'sad',
            'angry': 'angry',
            'disgust': 'angry'
        }
        
        mood = emotion_to_mood.get(emotion, 'happy')
        
        if mood == "happy":
            songs = [
                "Happy - Pharrell Williams",
                "Good Vibrations - The Beach Boys",
                "Don't Stop Me Now - Queen",
                "Walking on Sunshine - Katrina",
                "I Gotta Feeling - Black Eyed Peas"
            ]
        elif mood == "sad":
            songs = [
                "Someone Like You - Adele",
                "Hurt - Johnny Cash",
                "The Night We Met - Lord Huron",
                "Fix You - Coldplay",
                "Let Her Go - Passenger"
            ]
        else:
            songs = [
                "Break Stuff - Limp Bizkit",
                "Killing in the Name - RATM",
                "Enter Sandman - Metallica",
                "Bodies - Drowning Pool",
                "Smells Like Teen Spirit - Nirvana"
            ]
        
        return jsonify({
            'emotion': emotion,
            'mood': mood,
            'songs': songs
        })
        
    except Exception as e:
        print(f"Error in emotion detection: {e}")
        return jsonify({'error': str(e)}), 500

# TRENDING ARTISTS ROUTES
@app.route('/trending')
def trending_page():
    return render_template('trending.html')

@app.route('/api/trending-artists')
def get_trending_artists():
    """Curated trending artists - no API needed!"""
    try:
        trending_artists = [
            {
                'id': '1',
                'name': 'Taylor Swift',
                'image': 'https://i.scdn.co/image/ab6761610000e5ebe672b5f553298dcdccb0e676',
                'genres': ['pop', 'country'],
                'popularity': 100,
                'followers': 95000000,
                'spotify_url': 'https://open.spotify.com/artist/06HL4z0CvFAxyc27GXpf02'
            },
            {
                'id': '2',
                'name': 'Bad Bunny',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb19c2790744c792d05570bb71',
                'genres': ['latin', 'reggaeton'],
                'popularity': 99,
                'followers': 72000000,
                'spotify_url': 'https://open.spotify.com/artist/4q3ewBCX7sLwd24euuV69X'
            },
            {
                'id': '3',
                'name': 'The Weeknd',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb214f3cf1cbe7139c1e26ffbb',
                'genres': ['r&b', 'pop'],
                'popularity': 98,
                'followers': 68000000,
                'spotify_url': 'https://open.spotify.com/artist/1Xyo4u8uXC1ZmMpatF05PJ'
            },
            {
                'id': '4',
                'name': 'Drake',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb4293385d324db8558179afd9',
                'genres': ['hip hop', 'rap'],
                'popularity': 98,
                'followers': 76000000,
                'spotify_url': 'https://open.spotify.com/artist/3TVXtAsR1Inumwj472S9r4'
            },
            {
                'id': '5',
                'name': 'Ariana Grande',
                'image': 'https://i.scdn.co/image/ab6761610000e5ebb453c0e89347e97dbda45f9f',
                'genres': ['pop', 'r&b'],
                'popularity': 97,
                'followers': 87000000,
                'spotify_url': 'https://open.spotify.com/artist/66CXWjxzNUsdJxJ2JdwvnR'
            },
            {
                'id': '6',
                'name': 'Billie Eilish',
                'image': 'https://i.scdn.co/image/ab6761610000e5ebb0b94df59daecbdfe97e88d1',
                'genres': ['pop', 'alternative'],
                'popularity': 96,
                'followers': 105000000,
                'spotify_url': 'https://open.spotify.com/artist/6qqNVTkY8uBg9cP3Jd7DAH'
            },
            {
                'id': '7',
                'name': 'Ed Sheeran',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb3bcef85e105dfc42399ef0ba',
                'genres': ['pop', 'singer-songwriter'],
                'popularity': 95,
                'followers': 92000000,
                'spotify_url': 'https://open.spotify.com/artist/6eUKZXaKkcviH0Ku9w2n3V'
            },
            {
                'id': '8',
                'name': 'Dua Lipa',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb0c37534f9e5fad0ebd4f8993',
                'genres': ['pop', 'dance'],
                'popularity': 94,
                'followers': 48000000,
                'spotify_url': 'https://open.spotify.com/artist/6M2wZ9GZgrQXHCFfjv46we'
            },
            {
                'id': '9',
                'name': 'Post Malone',
                'image': 'https://i.scdn.co/image/ab6761610000e5ebfcd715dfbcf6ccb8b9858258',
                'genres': ['hip hop', 'pop'],
                'popularity': 93,
                'followers': 44000000,
                'spotify_url': 'https://open.spotify.com/artist/246dkjvS1zLTtiykXe5h60'
            },
            {
                'id': '10',
                'name': 'Olivia Rodrigo',
                'image': 'https://i.scdn.co/image/ab6761610000e5eba17e0e424327c0c2df9d2ec1',
                'genres': ['pop', 'rock'],
                'popularity': 92,
                'followers': 28000000,
                'spotify_url': 'https://open.spotify.com/artist/1McMsnEElThX1knmY4oliG'
            },
            {
                'id': '11',
                'name': 'SZA',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb0895066d172e1f51f520bc65',
                'genres': ['r&b', 'soul'],
                'popularity': 91,
                'followers': 25000000,
                'spotify_url': 'https://open.spotify.com/artist/7tYKF4w9nC0nq9CsPZTHyP'
            },
            {
                'id': '12',
                'name': 'Travis Scott',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb3c9df5d4ec01c4312e534b91',
                'genres': ['hip hop', 'trap'],
                'popularity': 90,
                'followers': 41000000,
                'spotify_url': 'https://open.spotify.com/artist/0Y5tJX1MQlPlqiwlOH1tJY'
            },
            {
                'id': '13',
                'name': 'Sabrina Carpenter',
                'image': 'https://i.scdn.co/image/ab6761610000e5ebb05d5f8cb1ff0e4238a893bd',
                'genres': ['pop'],
                'popularity': 89,
                'followers': 18000000,
                'spotify_url': 'https://open.spotify.com/artist/74KM79TiuVKeVCqs8QtB0B'
            },
            {
                'id': '14',
                'name': 'Bruno Mars',
                'image': 'https://i.scdn.co/image/ab6761610000e5ebe5a5e6aa9d2a22539579e987',
                'genres': ['pop', 'r&b', 'funk'],
                'popularity': 88,
                'followers': 50000000,
                'spotify_url': 'https://open.spotify.com/artist/0du5cEVh5yTK9QJze8zA0C'
            },
            {
                'id': '15',
                'name': 'Kendrick Lamar',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb4d55f7dfe83f41a05f7d84c4',
                'genres': ['hip hop', 'rap'],
                'popularity': 87,
                'followers': 35000000,
                'spotify_url': 'https://open.spotify.com/artist/2YZyLoL8N0Wb9xBt1NhZWg'
            },
            {
                'id': '16',
                'name': 'Rihanna',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb20923e5d37881b8668e07caf',
                'genres': ['pop', 'r&b'],
                'popularity': 86,
                'followers': 52000000,
                'spotify_url': 'https://open.spotify.com/artist/5pKCCKE2ajJHZ9KAiaK11H'
            },
            {
                'id': '17',
                'name': 'Harry Styles',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb58f75aa83f62f22f4c9edf38',
                'genres': ['pop', 'rock'],
                'popularity': 85,
                'followers': 42000000,
                'spotify_url': 'https://open.spotify.com/artist/6KImCVD70vtIoJWnq6nGn3'
            },
            {
                'id': '18',
                'name': 'Coldplay',
                'image': 'https://i.scdn.co/image/ab6761610000e5eba792d7a35a3f1827e0a42999',
                'genres': ['rock', 'alternative'],
                'popularity': 84,
                'followers': 38000000,
                'spotify_url': 'https://open.spotify.com/artist/4gzpq5DPGxSnKTe4SA8HAU'
            },
            {
                'id': '19',
                'name': 'Peso Pluma',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb8fa6b8c47c74506dbb06c0f0',
                'genres': ['regional mexican'],
                'popularity': 83,
                'followers': 22000000,
                'spotify_url': 'https://open.spotify.com/artist/12GqGscKJx3aE4t07u7eVZ'
            },
            {
                'id': '20',
                'name': 'Adele',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb32ba89cd576b37dfea8151e4',
                'genres': ['pop', 'soul'],
                'popularity': 82,
                'followers': 51000000,
                'spotify_url': 'https://open.spotify.com/artist/4dpARuHxo51G3z768sgnrY'
            }
        ]
        
        return jsonify({'success': True, 'artists': trending_artists})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/artist/<artist_id>/top-tracks')
def get_artist_top_tracks(artist_id):
    """Return sample top tracks"""
    try:
        tracks = [
            {
                'id': '1',
                'name': 'Popular Hit #1',
                'album': 'Latest Album',
                'album_image': 'https://via.placeholder.com/300',
                'preview_url': None,
                'duration_ms': 210000,
                'spotify_url': 'https://open.spotify.com'
            },
            {
                'id': '2',
                'name': 'Popular Hit #2',
                'album': 'Greatest Hits',
                'album_image': 'https://via.placeholder.com/300',
                'preview_url': None,
                'duration_ms': 195000,
                'spotify_url': 'https://open.spotify.com'
            }
        ]
        
        return jsonify({'success': True, 'tracks': tracks})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🎵 MOOD MUSIC RECOMMENDER")
    print("="*50)
    print("✓ Emotion Detection: ACTIVE")
    print("✓ Trending Artists: ACTIVE")
    print("="*50)
    # Pre-load DeepFace in background so first emotion detection isn't slow
    t = threading.Thread(target=_preload_deepface, daemon=True)
    t.start()
    print("✓ Server starting at http://127.0.0.1:5000")
    print("  (DeepFace loading in background - check terminal for progress)")
    print("="*50 + "\n")
    app.run(debug=True)
    