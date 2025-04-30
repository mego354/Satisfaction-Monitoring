from flask import Flask, request, render_template, Response, jsonify, session, redirect, url_for
from dotenv import load_dotenv
import os
from pymongo import MongoClient
import bcrypt
import cv2
import mediapipe as mp
import numpy as np
from utils.facial_expressions_detection import detect_facial_expression
from utils.hand_gesture_detection import detect_hand_gesture

# Load environment variables from the backend folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'backend', '.env'))

# Initialize Flask app
app = Flask(__name__)

# Set secret key from .env file
app.secret_key = os.getenv('SECRET_KEY')

# MongoDB connection
client = MongoClient(os.getenv('MONGO_URI'))
db = client['shehab']
users_collection = db['users']
scores_collection = db['scores']

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

# NEW CODE 
from datetime import datetime, timedelta
# Global variable to store latest health data
latest_health_data = {
    "timestamp": None,
    "heartRate": None,
    "spo2": None
}

@app.route('/health_data', methods=['POST'])
def receive_health_data():
    global latest_health_data
    data = request.get_json()
    print(f"Received health data: {data}")
 
    # Convert timestamp to datetime format
    latest_health_data['timestamp'] = datetime.now()
    latest_health_data['heartRate'] = data.get('heartRate')
    latest_health_data['spo2'] = data.get('spo2')
    print(jsonify({"status": "Health data received"}))
    return jsonify({"status": "Health data received"}), 200
# END NEW CODE 

# Function to draw face landmarks on a frame
def draw_face_landmarks(image, landmarks):
    for landmark in landmarks:
        x, y = int(landmark.x * image.shape[1]), int(landmark.y * image.shape[0])
        cv2.circle(image, (x, y), 2, (0, 255, 0), -1)

def draw_hand_landmarks(image, landmarks):
    for hand_landmarks in landmarks:
        for landmark in hand_landmarks.landmark:
            x, y = int(landmark.x * image.shape[1]), int(landmark.y * image.shape[0])
            cv2.circle(image, (x, y), 2, (255, 0, 0), -1)

def calculate_dynamic_satisfaction_score(hand_gesture, facial_expression):
    hand_gesture_scores = {
        'Thumbs Up': 1.0,
        'Thumbs Down': 0.0,
        'Fist': 0.5,
        'Open Hand': 0.6,
        'Pointing': 0.7
    }
    facial_expression_scores = {
        'Happy': 1.0,
        'Neutral': 0.6,
        'Sad': 0.2,
        'Angry': 0.1,
        'Surprise': 0.8,
        'Fear': 0.3,
        'Disgust': 0.4
    }

    hand_gesture_score = hand_gesture_scores.get(hand_gesture, 0.5)
    facial_expression_score = facial_expression_scores.get(facial_expression, 0.5)

    if facial_expression == 'Happy':
        facial_expression_score += 0.1
    if hand_gesture == 'Thumbs Up':
        hand_gesture_score += 0.2

    raw_score = 0.6 * hand_gesture_score + 0.4 * facial_expression_score

    # Health score penalty logic
    now = datetime.now()
    if latest_health_data["timestamp"] and (now - latest_health_data["timestamp"]) <= timedelta(seconds=20):
        heart_rate = latest_health_data["heartRate"]
        spo2 = latest_health_data["spo2"]

        # Always apply 75% base weight
        raw_score *= 0.65

        # Compute similarity (not penalty) to target values
        heart_similarity = max(1 - abs(heart_rate - 75) / 75, 0.0)  # 1.0 if perfect, 0.0 if very far
        spo2_similarity = max((spo2 - 90) / (95 - 90), 0.0) if spo2 < 95 else 1.0  # scaled for values under 95

        # Average health score (how good the data is)
        health_score = (heart_similarity + spo2_similarity) / 2
        health_bonus = health_score * 0.40  # Max regain is 25%

        print(f"Health bonus regained: {health_bonus:.2f}")

        raw_score += health_bonus  # Regain up to 25%

    return max(0.0, min(1.0, raw_score))


# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return "Email already exists.", 400

        users_collection.insert_one({'email': email, 'password': hashed_password})
        return redirect(url_for('login'))
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = users_collection.find_one({'email': email})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user_id'] = str(user['_id'])
            session['email'] = email
            return redirect(url_for('index'))
        return "Invalid email or password.", 401
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    return redirect(url_for('login'))

# Global variable to store the latest frame and satisfaction score
latest_frame = None
latest_hand_gesture = 'Unknown'
latest_facial_expression = 'Neutral'

# Video feed route
def generate_video_feed(email):
    global latest_frame, latest_hand_gesture, latest_facial_expression  # Use global variables to store values
    cap = cv2.VideoCapture(0)  # Use 0 for default camera, try 1 for external camera
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        try:
            # Convert frame to RGB for MediaPipe processing
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Face Mesh Processing (Detect Face Landmarks)
            results = face_mesh.process(rgb_frame)
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    draw_face_landmarks(frame, face_landmarks.landmark)
                try:
                    facial_expression = detect_facial_expression(rgb_frame)  # Real-time detection
                    print(f"Facial Expression Detected: {facial_expression}")
                except Exception as e:
                    print(f"Error detecting facial expression: {e}")
                    facial_expression = 'Unknown'
            else:
                facial_expression = 'Unknown'

            # Hand Gesture Processing
            hand_results = hands.process(rgb_frame)
            if hand_results.multi_hand_landmarks:
                draw_hand_landmarks(frame, hand_results.multi_hand_landmarks)
                try:
                    hand_gesture = detect_hand_gesture(rgb_frame)  # Real-time detection
                    print(f"Hand Gesture Detected: {hand_gesture}")
                except Exception as e:
                    print(f"Error detecting hand gesture: {e}")
                    hand_gesture = 'Unknown'
            else:
                hand_gesture = 'Unknown'

            # Update the global variables
            latest_hand_gesture = hand_gesture
            latest_facial_expression = facial_expression

            # Calculate the dynamic Satisfaction Score
            satisfaction_score = calculate_dynamic_satisfaction_score(latest_hand_gesture, latest_facial_expression)
            print(f"Satisfaction Score: {satisfaction_score}")
            
            # Save to database
            scores_collection.insert_one({"score": satisfaction_score, "email": email})

            # Display the score on the frame
            cv2.putText(frame, f"Satisfaction: {satisfaction_score:.2f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

            # Save the frame to the global variable for future use
            latest_frame = frame

            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = buffer.tobytes()

            # Yield the frame to the client
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

        except Exception as e:
            print(f"Error processing frame: {e}")

    cap.release()


@app.route('/video_feed')
def video_feed():
    print(session['email'])
    return Response(generate_video_feed(session['email']), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/satisfaction_score')
def satisfaction_score():
    """
    Endpoint to fetch the latest dynamic satisfaction score as a JSON object
    """
    if latest_frame is None:
        return jsonify({'error': 'No video frame available'}), 400

    # Calculate the dynamic satisfaction score using the latest hand gesture and facial expression
    satisfaction_score = calculate_dynamic_satisfaction_score(latest_hand_gesture, latest_facial_expression)

    # Return the dynamic satisfaction score as JSON
    return jsonify({'satisfaction_score': satisfaction_score})


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=os.getenv('PORT'))
