import streamlit as st
from emotion_detector import EmotionDetector
from spotify_recommender import SpotifyRecommender
from collections import Counter
import os
import tempfile
import logging
import time
import cv2
import numpy as np

# Setup logging
logging.basicConfig(filename="app_errors.log", level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Mood-Based Music Recommender",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_emotion' not in st.session_state:
    st.session_state.current_emotion = None
if 'emotion_detector' not in st.session_state:
    st.session_state.emotion_detector = None
if 'spotify_recommender' not in st.session_state:
    st.session_state.spotify_recommender = None
if 'save_results' not in st.session_state:
    st.session_state.save_results = False
if 'video_processor' not in st.session_state:
    st.session_state.video_processor = None

def initialize_services():
    """Initialize emotion detector and Spotify recommender"""
    if st.session_state.emotion_detector is None:
        st.session_state.emotion_detector = EmotionDetector()
    
    if st.session_state.spotify_recommender is None:
        client_id = os.getenv('SPOTIFY_CLIENT_ID') or st.secrets.get("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET') or st.secrets.get("SPOTIFY_CLIENT_SECRET")
        if not client_id or not client_secret:
            st.error("Spotify credentials not found. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.")
            st.stop()
        st.session_state.spotify_recommender = SpotifyRecommender(client_id, client_secret)

def display_recommendations(emotion, language):
    """Display music recommendations based on emotion"""
    if not emotion or not st.session_state.spotify_recommender:
        return
    
    recommendations = st.session_state.spotify_recommender.get_recommendations(emotion, language)
    if recommendations:
        st.write(f"🎵 **Recommended {language.capitalize()} Songs for {emotion.capitalize()} Mood:**")
        for song in recommendations:
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    if song['image_url']:
                        st.image(song['image_url'], width=100)
                with cols[1]:
                    st.write(f"**{song['name']}**")
                    st.write(f"By: {song['artist']}")
                    st.write(f"[Listen on Spotify]({song['url']})")
                    if song['preview_url']:
                        st.audio(song['preview_url'])
                st.markdown("---")
    else:
        st.warning(f"No {language} songs found for {emotion} mood. Try a different language or emotion.")

def process_camera_snapshot():
    """Process webcam snapshot for emotion detection"""
    camera_image = st.camera_input("Take a Snapshot", key="camera_snapshot")
    if camera_image is not None:
        try:
            file_bytes = np.asarray(bytearray(camera_image.getvalue()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            frame_emotions, rgb_frame = st.session_state.emotion_detector.process_frame(frame, is_image=True)
            st.session_state.emotion_detector.emotion_history.extend(frame_emotions)
            st.session_state.emotion_detector.frame_count += 1
            
            for face_data in st.session_state.emotion_detector.detected_faces[-5:]:
                if time.time() - face_data['timestamp'] < 5:
                    x, y, w, h = face_data['box']
                    cv2.rectangle(rgb_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(rgb_frame, f"{face_data['emotion']}: {face_data['confidence']:.1f}%", 
                                (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            st.image(rgb_frame, channels="RGB", caption="Captured Snapshot")
            if frame_emotions:
                st.session_state.current_emotion = Counter(frame_emotions).most_common(1)[0][0]
        except Exception as e:
            logging.error(f"Snapshot processing error: {str(e)}")
            st.error(f"Error processing snapshot: {str(e)}")

def process_uploaded_image():
    """Process uploaded image for emotion detection"""
    uploaded_file = st.file_uploader("Upload an image", type=['jpg', 'jpeg', 'png'])
    if uploaded_file is not None:
        try:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            frame_emotions, rgb_frame = st.session_state.emotion_detector.process_frame(frame, is_image=True)
            st.session_state.emotion_detector.emotion_history.extend(frame_emotions)
            st.session_state.emotion_detector.frame_count += 1
            
            for face_data in st.session_state.emotion_detector.detected_faces[-5:]:
                if time.time() - face_data['timestamp'] < 5:
                    x, y, w, h = face_data['box']
                    cv2.rectangle(rgb_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(rgb_frame, f"{face_data['emotion']}: {face_data['confidence']:.1f}%", 
                                (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            st.image(rgb_frame, channels="RGB", caption="Uploaded Image")
            if frame_emotions:
                st.session_state.current_emotion = Counter(frame_emotions).most_common(1)[0][0]
        except Exception as e:
            logging.error(f"Image processing error: {str(e)}")
            st.error(f"Error processing image: {str(e)}")

def process_uploaded_video():
    """Process uploaded video file for emotion detection and display dominant emotion"""
    uploaded_file = st.file_uploader("Upload a video file", type=['mp4', 'avi', 'mov'])
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(uploaded_file.read())
            video_path = tmp_file.name
        
        st.video(uploaded_file)
        col1, col2 = st.columns(2)
        with col1:
            duration = st.slider("Processing Duration (seconds)", 10, 60, 30)
        with col2:
            max_frames = st.slider("Maximum Frames to Process", 50, 300, 150)
        
        if st.button("Process Video"):
            with st.spinner("Processing video..."):
                try:
                    video_processor = EmotionDetector()
                    emotions = video_processor.process_video(
                        video_path,
                        duration_seconds=duration,
                        max_frames=max_frames
                    )
                    if emotions:
                        emotion_counts = Counter(emotions)
                        dominant_emotion = emotion_counts.most_common(1)[0][0]
                        st.session_state.current_emotion = dominant_emotion
                        st.session_state.video_processor = video_processor
                        st.success("Video processing completed!")
                        # Display the dominant emotion
                        st.markdown(f"**The video primarily conveys a {dominant_emotion.capitalize()} emotion.**")
                    else:
                        st.warning("No emotions detected in the video.")
                except Exception as e:
                    logging.error(f"Video processing error: {str(e)}")
                    st.error(f"Error processing video: {str(e)}")
                finally:
                    try:
                        os.unlink(video_path)
                    except:
                        pass

def main():
    st.write("**Note**: Ensure you have installed `streamlit`, `opencv-python`, `deepface`, `mtcnn`, `pandas`, `seaborn`, `matplotlib`, `spotipy`, and `python-dotenv`.")
    initialize_services()
    
    st.title("Mood-Based Music Recommendation System 🎵")
    st.write("This app detects your emotions from snapshots, images, or videos and recommends music based on your mood!")
    
    st.sidebar.title("Settings")
    language = st.sidebar.selectbox("Select Language for Songs:", ["English", "Hindi", "Telugu"], index=0)
    if st.sidebar.button("Save Current Session"):
        if st.session_state.emotion_detector:
            st.session_state.emotion_detector.save_results()
        if st.session_state.video_processor:
            st.session_state.video_processor.save_results()
    if st.sidebar.button("Reset Detection"):
        st.session_state.emotion_detector = None
        st.session_state.video_processor = None
        st.session_state.current_emotion = None
        st.session_state.save_results = False
        st.rerun()
    
    # Display Current Emotion in the sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Current Emotion")
    if st.session_state.current_emotion:
        st.sidebar.markdown(f"### 😊 **{st.session_state.current_emotion.capitalize()}**")
        if st.session_state.emotion_detector and st.session_state.emotion_detector.detected_faces:
            st.sidebar.write(f"Confidence: {st.session_state.emotion_detector.detected_faces[-1]['confidence']:.1f}%")
        elif st.session_state.video_processor and st.session_state.video_processor.detected_faces:
            st.sidebar.write(f"Confidence: {st.session_state.video_processor.detected_faces[-1]['confidence']:.1f}%")
    else:
        st.sidebar.write("No emotion detected yet.")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Snapshot Detection", 
        "Image/Video Analysis",
        "Music Recommendations", 
        "Analytics"
    ])
    
    with tab1:
        st.subheader("Snapshot Emotion Detection")
        st.write("Take a snapshot using your camera to detect emotions.")
        process_camera_snapshot()
    
    with tab2:
        st.subheader("Image/Video Emotion Analysis")
        input_option = st.radio("Choose input method:", ("Upload Image", "Upload Video"))
        if input_option == "Upload Image":
            process_uploaded_image()
        else:
            process_uploaded_video()
    
    with tab3:
        st.subheader("Music Recommendations")
        if st.session_state.current_emotion:
            display_recommendations(st.session_state.current_emotion, language)
        else:
            st.info("Take a snapshot, upload an image, or process a video to get music recommendations!")
    
    with tab4:
        st.subheader("Emotion Analytics")
        if st.session_state.emotion_detector and st.session_state.emotion_detector.emotion_history:
            st.session_state.emotion_detector.display_emotion_analytics()
        elif st.session_state.video_processor:
            st.session_state.video_processor.display_emotion_analytics()
        else:
            st.info("Take a snapshot, upload an image, or process a video to see emotion analytics!")

if __name__ == "__main__":
    main()
