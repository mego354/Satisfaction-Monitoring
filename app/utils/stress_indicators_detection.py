import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Load the pre-trained stress indicator model (ensure path is correct)
model = load_model(r"C:\Users\mahmo\OneDrive\Documents\workspace\Web\be\Sleep_health_and_lifestyle_dataset_logistic_model.h5 ")
# C:\Users\hp\Desktop\GRAD\

# Define stress levels based on your model's output
STRESS_LEVELS = ['Low', 'Medium', 'High']

def detect_stress_indicator(frame):
    """
    Detects stress level from a given frame.
    Args:
        frame (numpy.ndarray): Input image frame.
    Returns:
        str: Detected stress level.
    """
    # Preprocess the frame for stress detection model
    resized_frame = cv2.resize(frame, (128, 128))  # Resize to model's input size
    normalized_frame = resized_frame / 255.0  # Normalize pixel values
    reshaped_frame = np.reshape(normalized_frame, (1, 128, 128, 3))  # Reshape for model input

    # Predict stress level
    predictions = model.predict(reshaped_frame)
    stress_index = np.argmax(predictions)
    stress_level = STRESS_LEVELS[stress_index]

    return stress_level

def process_stress_for_satisfaction(frame):
    """
    Integrates stress detection into satisfaction detection framework.
    Args:
        frame (numpy.ndarray): Input image frame.
    Returns:
        dict: Stress indicator result for integration.
    """
    stress_level = detect_stress_indicator(frame)
    stress_result = {
        'stress_level': stress_level
    }
    return stress_result
