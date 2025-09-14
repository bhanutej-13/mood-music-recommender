import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import streamlit as st
import logging

# Setup logging
logging.basicConfig(filename="spotify_errors.log", level=logging.INFO)

# Constants
MAX_OFFSET = 950
SUPPORTED_LANGUAGES = ["hindi", "telugu", "english"]
MOOD_TO_GENRE = {
    "happy": "pop",
    "sad": "acoustic",
    "angry": "rock",
    "surprise": "electronic",
    "neutral": "indie",
    "fear": "ambient",
    "disgust": "metal"
}
LANGUAGE_KEYWORDS = {
    "hindi": [
        "Arijit", "Shreya", "Neha", "Kumar", "Jubin", "Sonu", "KK", "Rahat", "Mohit", "Atif", "Udit",
        "Lata", "Kishore", "Asha", "Sunidhi", "Alka", "Shaan", "Pritam", "Armaan", "Badshah",
        "Zindagi", "Dil", "Tera", "Mera", "Pyaar", "Ishq", "Mohabbat", "Yaad", "Saath", "Tum", "Hum",
        "Jaan", "Pal", "Raat", "Sapna", "Chand", "Tujh", "Aankhon", "Leja", "Bekhayali",
        "Bollywood", "Hindi", "Desi", "India", "Mumbai", "Aashiqui", "Kalank", "Kabir", "Dostana",
        "Punjabi", "Lofi", "Romantic", "Mashup", "Bolna", "Baarish", "Love Story"
    ],
    "telugu": [
        "Sid", "Sagar", "Anirudh", "Devi", "Sri", "Prasad", "Chinmayi", "Hesham", "Thaman", "Ramya", "Vishal",
        "S.P.", "Balasubrahmanyam", "Srinivas", "Shankar", "Geetha", "Madhavi", "Harini", "Karthik",
        "Prema", "Manasu", "Pranayam", "Naa", "Nee", "Kala", "Oka", "Chinni", "Gunde", "Aakasam", "Ninne",
        "Tollywood", "Telugu", "Andhra", "Hyderabad", "Nuvvu", "Cheli", "Priya", "Gundello", "Adbhutam",
        "Melody", "Romantic", "Mass", "Item", "Raaga", "Sankranthi", "Diwali"
    ],
    "english": []
}

class SpotifyRecommender:
    AVAILABLE_GENRES = {
        'hindi': ['indian', 'bollywood'],
        'telugu': ['indian'],
        'english': [
            'alternative', 'ambient', 'blues', 'classical', 'country',
            'dance', 'electronic', 'folk', 'funk', 'hip-hop', 'house',
            'indie', 'jazz', 'metal', 'pop', 'punk', 'r-n-b', 'rock',
            'soul', 'study'
        ]
    }

    EMOTION_PARAMS = {
        'happy': {
            'seed_genres': {
                'english': ['pop', 'dance', 'funk'],
                'hindi': ['bollywood'],
                'telugu': ['indian']
            },
            'audio_features': {
                'valence': (0.6, 1.0, 0.8),
                'energy': (0.6, 1.0, 0.8),
                'danceability': (0.6, 1.0, 0.8)
            },
            'search_terms': {
                'english': ['happy', 'upbeat', 'cheerful', 'joy'],
                'hindi': ['happy bollywood', 'dance bollywood', 'upbeat hindi'],
                'telugu': ['happy telugu', 'dance telugu', 'upbeat telugu']
            }
        },
        'sad': {
            'seed_genres': {
                'english': ['acoustic', 'study', 'classical'],
                'hindi': ['bollywood'],
                'telugu': ['indian']
            },
            'audio_features': {
                'valence': (0.0, 0.4, 0.2),
                'energy': (0.0, 0.4, 0.2),
                'danceability': (0.2, 0.5, 0.35)
            },
            'search_terms': {
                'english': ['sad', 'emotional', 'melancholy', 'heartbreak'],
                'hindi': ['sad bollywood', 'emotional hindi', 'sad hindi songs'],
                'telugu': ['sad telugu', 'emotional telugu', 'telugu melody']
            }
        },
        'angry': {
            'seed_genres': {
                'english': ['rock', 'metal', 'electronic'],
                'hindi': ['bollywood'],
                'telugu': ['indian']
            },
            'audio_features': {
                'valence': (0.0, 0.4, 0.2),
                'energy': (0.7, 1.0, 0.85),
                'danceability': (0.4, 0.8, 0.6)
            },
            'search_terms': {
                'english': ['angry', 'intense', 'powerful', 'rage'],
                'hindi': ['powerful bollywood', 'intense hindi', 'energetic hindi'],
                'telugu': ['powerful telugu', 'intense telugu', 'mass telugu']
            }
        },
        'neutral': {
            'seed_genres': {
                'english': ['indie', 'folk', 'study'],
                'hindi': ['bollywood'],
                'telugu': ['indian']
            },
            'audio_features': {
                'valence': (0.4, 0.6, 0.5),
                'energy': (0.4, 0.6, 0.5),
                'danceability': (0.4, 0.6, 0.5)
            },
            'search_terms': {
                'english': ['relaxing', 'calm', 'peaceful', 'ambient'],
                'hindi': ['relaxing bollywood', 'peaceful hindi', 'calm hindi'],
                'telugu': ['relaxing telugu', 'peaceful telugu', 'melody telugu']
            }
        },
        'surprise': {
            'seed_genres': {
                'english': ['electronic', 'dance', 'house'],
                'hindi': ['bollywood'],
                'telugu': ['indian']
            },
            'audio_features': {
                'valence': (0.6, 1.0, 0.8),
                'energy': (0.7, 1.0, 0.85),
                'danceability': (0.6, 1.0, 0.8)
            },
            'search_terms': {
                'english': ['energetic', 'exciting', 'upbeat', 'party'],
                'hindi': ['party bollywood', 'dance hindi', 'celebration hindi'],
                'telugu': ['party telugu', 'dance telugu', 'celebration telugu']
            }
        },
        'fear': {
            'seed_genres': {
                'english': ['ambient', 'classical', 'electronic'],
                'hindi': ['bollywood'],
                'telugu': ['indian']
            },
            'audio_features': {
                'valence': (0.0, 0.4, 0.2),
                'energy': (0.3, 0.7, 0.5),
                'danceability': (0.2, 0.5, 0.35)
            },
            'search_terms': {
                'english': ['dark', 'mysterious', 'intense', 'atmospheric'],
                'hindi': ['mysterious bollywood', 'intense hindi', 'dark hindi'],
                'telugu': ['mysterious telugu', 'intense telugu', 'dark telugu']
            }
        },
        'disgust': {
            'seed_genres': {
                'english': ['metal', 'rock', 'electronic'],
                'hindi': ['bollywood'],
                'telugu': ['indian']
            },
            'audio_features': {
                'valence': (0.0, 0.4, 0.2),
                'energy': (0.7, 1.0, 0.85),
                'danceability': (0.4, 0.7, 0.55)
            },
            'search_terms': {
                'english': ['intense', 'heavy', 'dark', 'powerful'],
                'hindi': ['intense bollywood', 'powerful hindi', 'dark hindi'],
                'telugu': ['intense telugu', 'powerful telugu', 'dark telugu']
            }
        }
    }

    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id or os.getenv('SPOTIFY_CLIENT_ID') or st.secrets.get("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv('SPOTIFY_CLIENT_SECRET') or st.secrets.get("SPOTIFY_CLIENT_SECRET")
        self.sp = self._initialize_spotify()
        self.market = 'IN'

    def _initialize_spotify(self):
        try:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            return spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        except Exception as e:
            logging.error(f"Spotify initialization error: {str(e)}")
            st.error(f"Error initializing Spotify client: {str(e)}")
            return None

    def get_recommendations(self, emotion, language='english', limit=5):
        if not self.sp:
            st.error("Spotify client not initialized")
            return []

        if emotion not in self.EMOTION_PARAMS:
            st.warning(f"Unknown emotion: {emotion}")
            return []

        language = language.lower()
        emotion = emotion.lower()

        try:
            songs = self.search_songs(emotion, language, limit)
            if songs:
                return songs

            params = self.EMOTION_PARAMS[emotion]
            audio_features = params['audio_features']

            seed_tracks = []
            for term in params['search_terms'][language]:
                try:
                    results = self.sp.search(
                        q=term,
                        type='track',
                        limit=2,
                        market=self.market
                    )
                    if results['tracks']['items']:
                        track_id = results['tracks']['items'][0]['id']
                        if track_id not in seed_tracks:
                            seed_tracks.append(track_id)
                        if len(seed_tracks) >= 2:
                            break
                except Exception as e:
                    logging.warning(f"Search error for term '{term}': {str(e)}")
                    continue

            available_genres = self.AVAILABLE_GENRES[language]
            seed_genres = [genre for genre in params['seed_genres'][language] if genre in available_genres]

            recommendation_params = {
                'limit': limit,
                'market': self.market,
                'target_valence': audio_features['valence'][2],
                'target_energy': audio_features['energy'][2],
                'target_danceability': audio_features['danceability'][2],
                'min_valence': audio_features['valence'][0],
                'max_valence': audio_features['valence'][1],
                'min_energy': audio_features['energy'][0],
                'max_energy': audio_features['energy'][1],
                'min_danceability': audio_features['danceability'][0],
                'max_danceability': audio_features['danceability'][1]
            }

            if seed_tracks:
                recommendation_params['seed_tracks'] = seed_tracks[:2]
                if seed_genres:
                    recommendation_params['seed_genres'] = seed_genres[:3-len(seed_tracks)]
            elif seed_genres:
                recommendation_params['seed_genres'] = seed_genres[:5]
            else:
                recommendation_params['seed_genres'] = self.EMOTION_PARAMS[emotion]['seed_genres']['english'][:5]

            try:
                recommendations = self.sp.recommendations(**recommendation_params)
                songs = []
                for track in recommendations['tracks']:
                    songs.append({
                        'name': track['name'],
                        'artist': track['artists'][0]['name'],
                        'url': track['external_urls']['spotify'],
                        'preview_url': track['preview_url'],
                        'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None
                    })
                if songs:
                    return songs
            except Exception as e:
                logging.error(f"Recommendation error: {str(e)}")

            return self.search_songs(emotion, language, limit)
        except Exception as e:
            logging.error(f"Error getting recommendations: {str(e)}")
            st.error(f"Error getting recommendations: {str(e)}")
            return []

    def search_songs(self, emotion, language='english', limit=5):
        if not self.sp:
            return []

        try:
            search_terms = self.EMOTION_PARAMS[emotion]['search_terms'][language]
            for term in search_terms:
                try:
                    results = self.sp.search(
                        q=term,
                        limit=limit,
                        type='track',
                        market=self.market
                    )
                    if results['tracks']['items']:
                        songs = []
                        for track in results['tracks']['items']:
                            songs.append({
                                'name': track['name'],
                                'artist': track['artists'][0]['name'],
                                'url': track['external_urls']['spotify'],
                                'preview_url': track['preview_url'],
                                'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None
                            })
                        return songs
                except Exception as e:
                    logging.warning(f"Search error for term '{term}': {str(e)}")
                    continue
            return []
        except Exception as e:
            logging.error(f"Error searching songs: {str(e)}")
            st.error(f"Error searching songs: {str(e)}")
            return []

    def _is_language_match(self, text, language):
        if not text:
            return False
        text_lower = text.lower()
        if language == "english":
            ascii_ratio = sum(1 for char in text if ord(char) < 128) / len(text)
            return ascii_ratio > 0.5
        else:
            keywords = LANGUAGE_KEYWORDS.get(language.lower(), [])
            return any(keyword.lower() in text_lower for keyword in keywords)
