"""
MediScan AI - AI Model Module
CNN-based disease detector for chest X-rays and CT scans.
Uses a simulated model for hackathon demo with realistic prediction behavior.
Can be swapped with a real TensorFlow/Keras model by replacing the predict() function.
"""

import numpy as np
import cv2
import os

# Disease classes
CLASSES = ['Normal', 'Pneumonia', 'Tuberculosis']

# Detailed insights for each condition
INSIGHTS = {
    'Normal': [
        "No significant abnormalities detected in the lung fields.",
        "Heart size and mediastinal contours appear within normal limits.",
        "Costophrenic angles are clear bilaterally.",
        "No pleural effusion or pneumothorax identified.",
        "Overall lung parenchyma appears healthy."
    ],
    'Pneumonia': [
        "Abnormal lung opacity detected in the lower lobe regions.",
        "Pattern analysis indicates consolidation consistent with bacterial pneumonia.",
        "Air bronchograms may be present within the opacified region.",
        "Possible inflammation detected in the alveolar spaces.",
        "Recommended: Clinical correlation and follow-up imaging advised."
    ],
    'Tuberculosis': [
        "Upper lobe infiltrates detected with possible cavitary lesion.",
        "Pattern analysis shows features consistent with pulmonary tuberculosis.",
        "Fibrotic changes and nodular opacities identified in apical segments.",
        "Mediastinal lymphadenopathy may be present.",
        "Recommended: Sputum testing (AFB smear) and clinical evaluation advised."
    ]
}


def preprocess_image(image_path):
    """
    Preprocess a medical image for model input.
    Steps: Read → Resize to 224x224 → Normalize → Convert to array
    
    Args:
        image_path: Path to the medical scan image
    
    Returns:
        Preprocessed numpy array ready for prediction
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Could not read image file")

        # Convert to grayscale if needed (X-rays are typically grayscale)
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # Resize to model input size (224x224)
        resized = cv2.resize(gray, (224, 224))

        # Normalize pixel values to [0, 1]
        normalized = resized.astype(np.float32) / 255.0

        # Apply CLAHE for contrast enhancement (common in medical imaging)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(np.uint8(normalized * 255))
        normalized = enhanced.astype(np.float32) / 255.0

        return normalized

    except Exception as e:
        print(f"[Preprocess Error] {e}")
        return None


def predict(image_path):
    """
    Run disease prediction on a medical scan image.
    
    This uses a simulated model that analyzes image characteristics
    to generate realistic predictions. Replace this function with
    a real TensorFlow model for production use.
    
    Args:
        image_path: Path to the medical scan image
    
    Returns:
        dict with prediction, risk_score, confidence, and insights
    """
    try:
        preprocessed = preprocess_image(image_path)
        if preprocessed is None:
            return _error_result("Failed to preprocess image")

        # Analyze image characteristics for simulation
        mean_intensity = np.mean(preprocessed)
        std_intensity = np.std(preprocessed)
        
        # Use image statistics to generate varied but realistic predictions
        # This simulates what a real CNN would output
        np.random.seed(int(mean_intensity * 10000) % 2**31)
        
        # Generate prediction probabilities based on image features
        raw_scores = np.random.dirichlet([1.5, 2.0, 1.5])
        
        # Bias based on image characteristics
        if mean_intensity < 0.35:
            # Darker images - slightly more likely abnormal
            raw_scores[1] += 0.15
            raw_scores[2] += 0.10
        elif mean_intensity > 0.55:
            # Brighter/clearer images - slightly more likely normal
            raw_scores[0] += 0.20
        
        if std_intensity > 0.25:
            # High contrast - may indicate pathology
            raw_scores[1] += 0.10
            raw_scores[2] += 0.08

        # Normalize scores
        raw_scores = raw_scores / raw_scores.sum()
        
        # Get predicted class
        predicted_idx = np.argmax(raw_scores)
        predicted_class = CLASSES[predicted_idx]
        confidence = float(raw_scores[predicted_idx])
        
        # Calculate risk score
        risk_score = float(1.0 - raw_scores[0])  # Risk = 1 - P(Normal)
        
        # Ensure realistic ranges
        confidence = max(0.72, min(0.98, confidence))
        risk_score = max(0.05, min(0.95, risk_score))
        
        if predicted_class == 'Normal':
            risk_score = min(risk_score, 0.25)
            confidence = max(confidence, 0.85)

        # Get insights
        insights = INSIGHTS.get(predicted_class, INSIGHTS['Normal'])

        return {
            'success': True,
            'prediction': predicted_class,
            'risk_score': round(risk_score * 100, 1),
            'confidence': round(confidence * 100, 1),
            'insights': insights,
            'probabilities': {
                'Normal': round(float(raw_scores[0]) * 100, 1),
                'Pneumonia': round(float(raw_scores[1]) * 100, 1),
                'Tuberculosis': round(float(raw_scores[2]) * 100, 1)
            }
        }

    except Exception as e:
        print(f"[Prediction Error] {e}")
        return _error_result(str(e))


def _error_result(message):
    """Return a standardized error result."""
    return {
        'success': False,
        'prediction': 'Error',
        'risk_score': 0,
        'confidence': 0,
        'insights': [f"Analysis error: {message}"],
        'probabilities': {'Normal': 0, 'Pneumonia': 0, 'Tuberculosis': 0}
    }
