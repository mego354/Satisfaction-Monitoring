from tensorflow.keras.models import load_model # type: ignore
import cv2
import numpy as np

# Load the hand gesture model (update with your model path)
hand_gesture_model_path = (r"C:\Users\mahmo\OneDrive\Documents\workspace\Web\be\hand_gesture_Model.h5")
hand_gesture_model = load_model(hand_gesture_model_path)

def detect_hand_gesture(image):
    # Resize to what the model expects (224x224)
    image_resized = cv2.resize(image, (224, 224))
    
    # Ensure we have 3 color channels (RGB)
    if len(image_resized.shape) == 2:  # If grayscale
        image_resized = cv2.cvtColor(image_resized, cv2.COLOR_GRAY2RGB)
    elif image_resized.shape[2] == 1:  # If single channel
        image_resized = cv2.cvtColor(image_resized, cv2.COLOR_GRAY2RGB)
    
    # Add batch dimension
    image_resized = np.expand_dims(image_resized, axis=0)
    
    # Normalize pixel values (optional but recommended)
    image_resized = image_resized / 255.0
    
    # Predict gesture
    prediction = hand_gesture_model.predict(image_resized)
    gesture_label = np.argmax(prediction)
    
    gesture_mapping = {0: 'Thumbs Up', 1: 'Thumbs Down', 2: 'Fist', 3: 'Open Hand', 4: 'Pointing'}
    return gesture_mapping.get(gesture_label, 'Unknown')

