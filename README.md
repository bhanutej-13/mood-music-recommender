Basic Mood-Based Music Recommender
A simple Streamlit web application that takes a user-selected mood as input and recommends Hindi/English songs from Spotify.
Prerequisites

Python 3.8+
Spotify Developer account credentials (Client ID and Client Secret)

Setup

Clone the repository:git clone <your-repo-url>
cd mood_music_recommender


Install dependencies:pip install -r requirements.txt


Create a .env file in the project root with your Spotify credentials:SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret


Run the Streamlit app:streamlit run app.py



Usage

Select a mood from the dropdown menu (e.g., Happy, Sad, Angry).
The app fetches and displays up to 5 Hindi/English song recommendations from Spotify based on the selected mood.
Click the Spotify links to listen to the songs.

Notes

The app uses the Spotify Web API with Client Credentials Flow.
If the Spotify API is unavailable, it falls back to mock song recommendations.
Ensure the .env file is not committed to version control (use .gitignore).

License
MIT
