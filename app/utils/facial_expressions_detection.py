import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Load the facial expression model
facial_expression_model_path = (r"C:\Users\mahmo\OneDrive\Documents\workspace\Web\be\model.h5")
facial_expression_model = load_model(facial_expression_model_path)

def detect_facial_expression(image):
    """
    Detects facial expression using the pre-trained model.
    """
    # Convert to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Resize to the expected size (48x48)
    resized_image = cv2.resize(gray_image, (48, 48))
   

    # Normalize image and expand dimensions (required by Keras)
    image_expanded = np.expand_dims(resized_image, axis=0)  # Add batch dimension
    image_expanded = np.expand_dims(image_expanded, axis=-1)  # Add channel dimension for grayscale
    
    
    # Check the image shape (for debugging)
    print(f"Preprocessed Facial Image Shape: {image_expanded.shape}")

    # Predict expression
    prediction = facial_expression_model.predict(image_expanded)
    expression_label = np.argmax(prediction)
    
    # Expression mapping (check if this matches your model’s output classes)
    expression_mapping = {
        0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 
        4: 'Sad', 5: 'Surprise', 6: 'Neutral'
    }
    
    # Return detected expression
    return expression_mapping.get(expression_label, 'Unknown')

