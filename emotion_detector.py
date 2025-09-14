import streamlit as st
import cv2
import numpy as np
from deepface import DeepFace
from mtcnn import MTCNN
from collections import Counter
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import time
import os
import logging

# Setup logging
logging.basicConfig(filename="emotion_errors.log", level=logging.INFO)

class EmotionDetector:
    def __init__(self):
        self.detector = MTCNN()
        self.emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        self.emotion_history = []
        self.detected_faces = []
        self.frame_count = 0
        self.min_confidence = 0.8

    def preprocess_frame(self, frame):
        """Apply basic preprocessing to the frame"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return rgb_frame

    def detect_faces(self, frame):
        """Detect faces in a frame with error handling"""
        try:
            faces = self.detector.detect_faces(frame)
            return [face for face in faces if face['confidence'] > self.min_confidence]
        except Exception as e:
            logging.error(f"Face detection error: {str(e)}")
            return []

    def analyze_emotion(self, face_img):
        """Analyze emotion in a face image with error handling"""
        try:
            if len(face_img.shape) == 2:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2RGB)
            elif face_img.shape[2] == 1:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2RGB)

            result = DeepFace.analyze(
                face_img,
                actions=['emotion'],
                enforce_detection=False,
                detector_backend='mtcnn'
            )
            emotion = result[0]['dominant_emotion'].lower()
            confidence = result[0]['emotion'][emotion]
            return emotion, confidence
        except Exception as e:
            logging.error(f"Emotion analysis error: {str(e)}")
            return None, None

    def process_frame(self, frame, is_image=False):
        """Process a single frame or image to detect faces and emotions"""
        rgb_frame = self.preprocess_frame(frame)
        faces = self.detect_faces(rgb_frame)
        frame_emotions = []

        for face in faces:
            x, y, w, h = face['box']
            x, y = max(0, x), max(0, y)
            w = min(w, rgb_frame.shape[1] - x)
            h = min(h, rgb_frame.shape[0] - y)

            if w <= 10 or h <= 10:
                continue

            face_img = rgb_frame[y:y+h, x:x+w]
            if face_img.size == 0:
                continue

            emotion, confidence = self.analyze_emotion(face_img)
            if emotion and confidence and emotion in self.emotions:
                frame_emotions.append(emotion)
                self.detected_faces.append({
                    'image': face_img,
                    'emotion': emotion,
                    'confidence': confidence,
                    'timestamp': time.time(),
                    'box': (x, y, w, h)
                })

        self.emotion_history = self.emotion_history[-100:]  # Limit to last 100 emotions
        self.detected_faces = self.detected_faces[-100:]  # Limit to last 100 faces
        return frame_emotions, rgb_frame

    def process_video(self, video_path, duration_seconds=30, max_frames=150, frame_skip=5):
        """Process video file for emotion detection"""
        self.reset()
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logging.error(f"Could not open video file: {video_path}")
                st.error(f"Could not open video file: {video_path}")
                return []

            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                frame_skip = max(1, int(fps / 10))

            frame_count = 0
            processed_count = 0
            start_time = time.time()

            progress_bar = st.progress(0)
            status_text = st.empty()

            while frame_count < max_frames and (time.time() - start_time) < duration_seconds:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                if frame_count % frame_skip != 0:
                    continue

                progress = min(1.0, frame_count / max_frames)
                progress_bar.progress(progress)
                status_text.text(f"Processing frame {frame_count}/{max_frames}")

                frame_emotions, _ = self.process_frame(frame)
                self.emotion_history.extend(frame_emotions)
                processed_count += 1

            cap.release()
            progress_bar.empty()
            status_text.empty()

            if processed_count > 0:
                st.success(f"Processed {processed_count} frames with detected emotions")
                return self.emotion_history
            else:
                st.warning("No emotions detected in the video")
                return []
        except Exception as e:
            logging.error(f"Video processing error: {str(e)}")
            st.error(f"Error processing video: {str(e)}")
            return []
        finally:
            if 'cap' in locals() and cap is not None:
                cap.release()

    def display_emotion_analytics(self):
        """Display comprehensive emotion analytics in Streamlit"""
        if not self.emotion_history:
            st.warning("No emotions detected yet.")
            return

        emotion_counts = Counter(self.emotion_history)
        df = pd.DataFrame.from_dict(emotion_counts, orient='index', columns=['count'])
        df['percentage'] = (df['count'] / len(self.emotion_history)) * 100
        df = df.sort_values('count', ascending=False)

        st.subheader("Emotion Detection Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Emotions Detected", len(self.emotion_history))
        with col2:
            st.metric("Most Common Emotion", df.index[0])
        with col3:
            st.metric("Detection Rate", f"{df.iloc[0]['percentage']:.1f}%")

        st.subheader("Emotion Distribution")
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x=df.index, y=df['percentage'])
        plt.title("Emotion Distribution (%)")
        plt.xticks(rotation=45)
        plt.ylabel("Percentage")
        plt.xlabel("Emotion")
        st.pyplot(fig)

        if len(self.emotion_history) > 10:
            st.subheader("Emotion Timeline")
            fig, ax = plt.subplots(figsize=(10, 5))
            emotion_series = pd.Series(self.emotion_history)
            emotion_series.value_counts().plot(kind='pie', autopct='%1.1f%%')
            plt.title("Emotion Distribution Over Time")
            plt.ylabel('')
            st.pyplot(fig)

        if self.detected_faces:
            st.subheader("Recent Detections")
            cols = st.columns(4)
            for i, face in enumerate(self.detected_faces[-4:]):
                with cols[i]:
                    st.image(face['image'], caption=f"{face['emotion'].capitalize()}\n{face['confidence']:.1f}%", width=150)

    def reset(self):
        """Reset all emotion tracking data"""
        self.emotion_history.clear()
        self.detected_faces.clear()
        self.frame_count = 0

    def save_results(self, output_dir='results'):
        """Save detection results to files"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if self.emotion_history:
            history_file = os.path.join(output_dir, f'emotion_history_{time.strftime("%Y%m%d_%H%M%S")}.csv')
            df = pd.DataFrame({
                'emotion': self.emotion_history,
                'timestamp': [face['timestamp'] for face in self.detected_faces],
                'confidence': [face['confidence'] for face in self.detected_faces]
            })
            df.to_csv(history_file, index=False)
            st.success(f"Emotion history saved to {history_file}")

        if self.detected_faces:
            faces_dir = os.path.join(output_dir, 'detected_faces')
            if not os.path.exists(faces_dir):
                os.makedirs(faces_dir)

            for i, face_data in enumerate(self.detected_faces[-10:]):
                img_path = os.path.join(faces_dir, f"face_{i}_{face_data['emotion']}_{face_data['confidence']:.0f}.png")
                cv2.imwrite(img_path, cv2.cvtColor(face_data['image'], cv2.COLOR_RGB2BGR))
            st.success(f"Sample faces saved to {faces_dir}")