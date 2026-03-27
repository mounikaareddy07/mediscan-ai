"""
MediScan AI - AI Model Module (Real Model Inference)
Loads trained TFLite models for real disease detection.
Falls back to simulated predictions if models are not available.
Supports 5 scan types: chest_xray, brain_tumor, skin_lesion, retinal, bone_fracture
"""

import numpy as np
import cv2
import os
import json

# ─── Configuration ───────────────────────────────────────────────────
IMG_SIZE = 150  # Must match training size
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Try to import TFLite runtime ────────────────────────────────────
tflite_interpreter = None
try:
    import tflite_runtime.interpreter as tflite
    tflite_interpreter = tflite
    print("[AI Model] Using tflite-runtime for inference")
except ImportError:
    try:
        import tensorflow as tf
        tflite_interpreter = tf.lite
        print("[AI Model] Using TensorFlow Lite for inference")
    except ImportError:
        print("[AI Model] No TFLite runtime found — using simulated predictions")

# ─── Model Registry ─────────────────────────────────────────────────
# Each entry: model_name -> {interpreter, classes, loaded}
MODELS = {}

# Scan type configuration
SCAN_TYPES = {
    'chest_xray': {
        'model_file': 'chest_xray_model.tflite',
        'classes_file': 'chest_xray_model_classes.json',
        'display_name': 'Chest X-ray',
        'default_classes': ['NORMAL', 'PNEUMONIA'],
        'description': 'Detects pneumonia from chest X-ray images'
    },
    'brain_tumor': {
        'model_file': 'brain_tumor_model.tflite',
        'classes_file': 'brain_tumor_model_classes.json',
        'display_name': 'Brain Tumor MRI',
        'default_classes': ['glioma', 'meningioma', 'notumor', 'pituitary'],
        'description': 'Classifies brain tumors from MRI scans'
    },
    'skin_lesion': {
        'model_file': 'skin_lesion_model.tflite',
        'classes_file': 'skin_lesion_model_classes.json',
        'display_name': 'Skin Lesion',
        'default_classes': ['benign', 'malignant'],
        'description': 'Detects malignant skin lesions (melanoma)'
    },
    'retinal': {
        'model_file': 'retinal_model.tflite',
        'classes_file': 'retinal_model_classes.json',
        'display_name': 'Retinal OCT',
        'default_classes': ['CNV', 'DME', 'DRUSEN', 'NORMAL'],
        'description': 'Detects retinal diseases from OCT scans'
    },
    'bone_fracture': {
        'model_file': 'bone_fracture_model.tflite',
        'classes_file': 'bone_fracture_model_classes.json',
        'display_name': 'Bone X-ray',
        'default_classes': ['fractured', 'not fractured'],
        'description': 'Detects bone fractures from X-ray images'
    }
}

# ─── Detailed insights for each condition ────────────────────────────
INSIGHTS = {
    # Chest X-ray
    'NORMAL': [
        "No significant abnormalities detected in the lung fields.",
        "Heart size and mediastinal contours appear within normal limits.",
        "Costophrenic angles are clear bilaterally.",
        "No pleural effusion or pneumothorax identified.",
        "Overall lung parenchyma appears healthy."
    ],
    'PNEUMONIA': [
        "Abnormal lung opacity detected in the lower lobe regions.",
        "Pattern analysis indicates consolidation consistent with pneumonia.",
        "Air bronchograms may be present within the opacified region.",
        "Possible inflammation detected in the alveolar spaces.",
        "Recommended: Clinical correlation and follow-up imaging advised."
    ],
    # Brain Tumor
    'glioma': [
        "Irregular mass detected with features consistent with glioma.",
        "Infiltrative growth pattern observed in brain parenchyma.",
        "Possible contrast enhancement suggesting higher-grade lesion.",
        "Surrounding edema detected in the affected region.",
        "Recommended: Neurosurgical consultation and advanced imaging."
    ],
    'meningioma': [
        "Well-defined extra-axial mass detected with dural attachment.",
        "Homogeneous enhancement pattern consistent with meningioma.",
        "Mass effect observed on adjacent brain structures.",
        "Dural tail sign may be present.",
        "Recommended: Neurosurgical evaluation for treatment planning."
    ],
    'notumor': [
        "No tumors or mass lesions detected in the brain.",
        "Brain parenchyma appears normal without significant abnormalities.",
        "Ventricular system appears symmetrical and normal in size.",
        "No midline shift or mass effect identified.",
        "Overall brain structures appear within normal limits."
    ],
    'pituitary': [
        "Sellar/parasellar mass detected consistent with pituitary tumor.",
        "Pituitary gland appears enlarged with possible adenoma.",
        "Optic chiasm may be compressed by the mass.",
        "Recommended: Endocrine evaluation and hormonal assessment.",
        "MRI with gadolinium enhancement advised for detailed evaluation."
    ],
    # Skin Lesion
    'benign': [
        "Skin lesion appears to have benign characteristics.",
        "Regular borders and uniform color distribution observed.",
        "No signs of asymmetry or irregular pigmentation.",
        "Dermatoscopic patterns consistent with benign lesion.",
        "Recommended: Regular monitoring and follow-up examination."
    ],
    'malignant': [
        "⚠️ Skin lesion shows features concerning for malignancy.",
        "Irregular borders and asymmetric shape detected.",
        "Color variation and uneven pigmentation observed.",
        "Pattern analysis suggests possible melanoma or carcinoma.",
        "Recommended: URGENT dermatological consultation and biopsy."
    ],
    # Retinal
    'CNV': [
        "Choroidal neovascularization (CNV) detected in retinal scan.",
        "Abnormal blood vessel growth observed beneath the retina.",
        "Fluid accumulation and retinal thickening present.",
        "Features consistent with wet age-related macular degeneration.",
        "Recommended: Urgent ophthalmologic consultation for treatment."
    ],
    'DME': [
        "Diabetic macular edema (DME) detected in retinal scan.",
        "Fluid accumulation in the macula due to diabetic retinopathy.",
        "Retinal thickening and possible cystoid changes observed.",
        "Hard exudates may be present near the fovea.",
        "Recommended: Anti-VEGF treatment evaluation by ophthalmologist."
    ],
    'DRUSEN': [
        "Drusen deposits detected in the retinal scan.",
        "Yellow-white deposits accumulated beneath the retina.",
        "Early signs of age-related macular degeneration.",
        "Central vision monitoring recommended.",
        "Recommended: Regular eye exams and antioxidant supplements."
    ],
    # Bone Fracture
    'fractured': [
        "⚠️ Fracture detected in the bone X-ray image.",
        "Discontinuity in bone cortex identified.",
        "Possible displacement or angulation at fracture site.",
        "Surrounding soft tissue swelling may be present.",
        "Recommended: Orthopedic consultation for treatment planning."
    ],
    'not fractured': [
        "No fracture lines detected in the bone X-ray.",
        "Bone cortex appears intact and continuous.",
        "Joint spaces appear within normal limits.",
        "No signs of dislocation or subluxation.",
        "Bone density appears normal for patient demographics."
    ],
}

# Add fallback for common names
INSIGHTS['Normal'] = INSIGHTS['NORMAL']
INSIGHTS['Pneumonia'] = INSIGHTS['PNEUMONIA']
INSIGHTS['Tuberculosis'] = [
    "Upper lobe infiltrates detected with possible cavitary lesion.",
    "Pattern analysis shows features consistent with pulmonary tuberculosis.",
    "Fibrotic changes and nodular opacities identified in apical segments.",
    "Mediastinal lymphadenopathy may be present.",
    "Recommended: Sputum testing (AFB smear) and clinical evaluation advised."
]


def load_models():
    """Load all available TFLite models at startup."""
    global MODELS
    
    if tflite_interpreter is None:
        print("[AI Model] No TFLite runtime — all scan types will use simulation")
        return
    
    for scan_type, config in SCAN_TYPES.items():
        model_path = os.path.join(MODEL_DIR, config['model_file'])
        classes_path = os.path.join(MODEL_DIR, config['classes_file'])
        
        if os.path.exists(model_path):
            try:
                interpreter = tflite_interpreter.Interpreter(model_path=model_path)
                interpreter.allocate_tensors()
                
                # Load class mapping
                classes = config['default_classes']
                if os.path.exists(classes_path):
                    with open(classes_path, 'r') as f:
                        class_map = json.load(f)
                        classes = [class_map[str(i)] for i in range(len(class_map))]
                
                MODELS[scan_type] = {
                    'interpreter': interpreter,
                    'classes': classes,
                    'loaded': True
                }
                print(f"[AI Model] ✅ Loaded: {config['display_name']} ({len(classes)} classes)")
            except Exception as e:
                print(f"[AI Model] ❌ Failed to load {config['display_name']}: {e}")
        else:
            print(f"[AI Model] ⚠️ Not found: {config['model_file']} — will use simulation for {config['display_name']}")


def preprocess_image(image_path, target_size=IMG_SIZE):
    """
    Preprocess a medical image for model input.
    Returns a numpy array of shape (1, target_size, target_size, 3) normalized to [0, 1].
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Could not read image file")

        # Convert to RGB (OpenCV loads as BGR)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Resize to model input size
        resized = cv2.resize(img_rgb, (target_size, target_size))

        # Normalize to [0, 1]
        normalized = resized.astype(np.float32) / 255.0

        # Add batch dimension: (1, H, W, 3)
        batched = np.expand_dims(normalized, axis=0)

        return batched

    except Exception as e:
        print(f"[Preprocess Error] {e}")
        return None


def predict_with_model(image_path, scan_type):
    """Run real TFLite model inference."""
    if scan_type not in MODELS:
        return None
    
    model_info = MODELS[scan_type]
    interpreter = model_info['interpreter']
    classes = model_info['classes']
    
    # Preprocess
    input_data = preprocess_image(image_path)
    if input_data is None:
        return None
    
    # Get model input/output details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # Set input tensor
    interpreter.set_tensor(input_details[0]['index'], input_data)
    
    # Run inference
    interpreter.invoke()
    
    # Get output
    output_data = interpreter.get_tensor(output_details[0]['index'])
    probabilities = output_data[0]
    
    # Get prediction
    predicted_idx = np.argmax(probabilities)
    predicted_class = classes[predicted_idx]
    confidence = float(probabilities[predicted_idx])
    
    # Build probability dict
    prob_dict = {}
    for i, cls in enumerate(classes):
        prob_dict[cls] = round(float(probabilities[i]) * 100, 1)
    
    return {
        'prediction': predicted_class,
        'confidence': round(confidence * 100, 1),
        'probabilities': prob_dict,
        'classes': classes,
        'real_model': True
    }


def predict_simulated(image_path, scan_type):
    """Simulated prediction when no trained model is available."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Could not read image")
        
        # Get image stats for varied predictions
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        resized = cv2.resize(gray, (IMG_SIZE, IMG_SIZE))
        normalized = resized.astype(np.float32) / 255.0
        
        mean_val = np.mean(normalized)
        std_val = np.std(normalized)
        
        # Get classes for this scan type
        config = SCAN_TYPES.get(scan_type, SCAN_TYPES['chest_xray'])
        classes = config['default_classes']
        num_classes = len(classes)
        
        # Generate varied predictions based on image features
        np.random.seed(int(mean_val * 10000) % 2**31)
        raw_scores = np.random.dirichlet([2.0] * num_classes)
        
        # Bias based on image characteristics
        if mean_val < 0.35:
            # Darker images — slightly more likely abnormal
            for i in range(1, num_classes):
                raw_scores[i] += 0.1
        elif mean_val > 0.55:
            # Brighter images — slightly more likely normal
            raw_scores[0] += 0.15
        
        # Normalize
        raw_scores = raw_scores / raw_scores.sum()
        
        predicted_idx = np.argmax(raw_scores)
        predicted_class = classes[predicted_idx]
        confidence = float(raw_scores[predicted_idx])
        
        # Build probability dict
        prob_dict = {}
        for i, cls in enumerate(classes):
            prob_dict[cls] = round(float(raw_scores[i]) * 100, 1)
        
        # Clamp confidence to realistic range
        confidence = max(0.72, min(0.96, confidence))
        
        return {
            'prediction': predicted_class,
            'confidence': round(confidence * 100, 1),
            'probabilities': prob_dict,
            'classes': classes,
            'real_model': False
        }
    except Exception as e:
        print(f"[Simulated Predict Error] {e}")
        return None


def predict(image_path, scan_type='chest_xray'):
    """
    Main prediction function. Uses real model if available, else simulated.
    
    Args:
        image_path: Path to the medical scan image
        scan_type: One of 'chest_xray', 'brain_tumor', 'skin_lesion', 'retinal', 'bone_fracture'
    
    Returns:
        dict with prediction, risk_score, confidence, insights, probabilities
    """
    try:
        # Try real model first
        result = predict_with_model(image_path, scan_type)
        
        # Fall back to simulation
        if result is None:
            result = predict_simulated(image_path, scan_type)
        
        if result is None:
            return _error_result("Failed to process image")
        
        predicted_class = result['prediction']
        confidence = result['confidence']
        probabilities = result['probabilities']
        classes = result['classes']
        is_real = result['real_model']
        
        # Calculate risk score
        # For scan types with a "normal" class, risk = 1 - P(normal)
        normal_keys = ['NORMAL', 'Normal', 'notumor', 'not fractured', 'benign']
        normal_prob = 0
        for key in normal_keys:
            if key in probabilities:
                normal_prob = probabilities[key]
                break
        
        risk_score = round(100.0 - normal_prob, 1)
        
        # Get insights
        insights = INSIGHTS.get(predicted_class, [
            f"Analysis detected: {predicted_class}",
            f"Confidence level: {confidence}%",
            "Please consult a healthcare professional for proper evaluation.",
            "This is an AI-assisted screening tool, not a definitive diagnosis.",
            "Follow-up clinical examination is recommended."
        ])
        
        # Add model status note
        if not is_real:
            insights = insights + [
                "⚠️ Note: This prediction uses a simulated model. Upload trained model files for real AI analysis."
            ]
        
        return {
            'success': True,
            'prediction': predicted_class,
            'risk_score': risk_score,
            'confidence': confidence,
            'insights': insights,
            'probabilities': probabilities,
            'scan_type': scan_type,
            'scan_type_display': SCAN_TYPES.get(scan_type, {}).get('display_name', scan_type),
            'real_model': is_real
        }

    except Exception as e:
        print(f"[Prediction Error] {e}")
        return _error_result(str(e))


def get_available_models():
    """Return info about which models are loaded."""
    status = {}
    for scan_type, config in SCAN_TYPES.items():
        loaded = scan_type in MODELS
        status[scan_type] = {
            'display_name': config['display_name'],
            'description': config['description'],
            'loaded': loaded,
            'classes': MODELS[scan_type]['classes'] if loaded else config['default_classes']
        }
    return status


def _error_result(message):
    """Return a standardized error result."""
    return {
        'success': False,
        'prediction': 'Error',
        'risk_score': 0,
        'confidence': 0,
        'insights': [f"Analysis error: {message}"],
        'probabilities': {},
        'scan_type': 'unknown',
        'real_model': False
    }


# ─── Load models on import ──────────────────────────────────────────
load_models()
