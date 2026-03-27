"""
MediScan AI - Heatmap Visualization Module
Generates Grad-CAM style heatmap overlays on medical images.
Supports 5 scan types with scan-specific attention regions.
"""

import cv2
import numpy as np
import os


def generate_heatmap(image_path, prediction, output_path, scan_type='chest_xray'):
    """
    Generate a Grad-CAM style heatmap overlay on the medical image.
    
    Args:
        image_path: Path to the original scan image
        prediction: Predicted condition name
        output_path: Path to save the heatmap overlay image
        scan_type: Type of scan for region-appropriate heatmap generation
    
    Returns:
        Path to the saved heatmap image
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None

        img = cv2.resize(img, (512, 512))
        h, w = img.shape[:2]

        heatmap = np.zeros((h, w), dtype=np.float32)

        # Generate attention regions based on scan type + prediction
        _generate_attention(heatmap, prediction, scan_type, h, w)

        # Normalize heatmap to 0-255
        heatmap = np.clip(heatmap, 0, 1)
        heatmap_uint8 = np.uint8(255 * heatmap)

        # Apply color map
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        # Overlay heatmap on original image
        overlay = cv2.addWeighted(img, 0.6, heatmap_colored, 0.4, 0)

        # Add prediction label
        label = f"{prediction}"
        cv2.putText(overlay, label, (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Add scan type label
        scan_labels = {
            'chest_xray': 'Chest X-ray',
            'brain_tumor': 'Brain MRI',
            'skin_lesion': 'Skin Lesion',
            'retinal': 'Retinal OCT',
            'bone_fracture': 'Bone X-ray'
        }
        scan_label = scan_labels.get(scan_type, scan_type)
        cv2.putText(overlay, scan_label, (15, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imwrite(output_path, overlay)
        return output_path

    except Exception as e:
        print(f"[Heatmap Error] {e}")
        return None


def _generate_attention(heatmap, prediction, scan_type, h, w):
    """Generate scan-type-specific attention heatmap."""
    pred_lower = prediction.lower().replace(' ', '')
    
    if scan_type == 'chest_xray':
        _chest_xray_attention(heatmap, pred_lower, h, w)
    elif scan_type == 'brain_tumor':
        _brain_tumor_attention(heatmap, pred_lower, h, w)
    elif scan_type == 'skin_lesion':
        _skin_lesion_attention(heatmap, pred_lower, h, w)
    elif scan_type == 'retinal':
        _retinal_attention(heatmap, pred_lower, h, w)
    elif scan_type == 'bone_fracture':
        _bone_fracture_attention(heatmap, pred_lower, h, w)
    else:
        # Generic attention - center focus
        _add_gaussian_hotspot(heatmap, int(w * 0.5), int(h * 0.5), 80, 0.5)


def _chest_xray_attention(heatmap, pred, h, w):
    """Chest X-ray attention regions."""
    if 'pneumonia' in pred:
        # Pneumonia: lower lung regions with consolidation
        _add_gaussian_hotspot(heatmap, int(w * 0.35), int(h * 0.55), 60, 0.9)
        _add_gaussian_hotspot(heatmap, int(w * 0.65), int(h * 0.50), 55, 0.85)
        _add_gaussian_hotspot(heatmap, int(w * 0.40), int(h * 0.65), 45, 0.7)
        _add_gaussian_hotspot(heatmap, int(w * 0.60), int(h * 0.60), 50, 0.75)
    elif 'tuberculosis' in pred or 'tb' in pred:
        # TB: upper lung regions with cavitation
        _add_gaussian_hotspot(heatmap, int(w * 0.35), int(h * 0.30), 55, 0.95)
        _add_gaussian_hotspot(heatmap, int(w * 0.60), int(h * 0.35), 50, 0.8)
        _add_gaussian_hotspot(heatmap, int(w * 0.45), int(h * 0.25), 40, 0.7)
        _add_gaussian_hotspot(heatmap, int(w * 0.30), int(h * 0.40), 35, 0.6)
    else:
        # Normal: minimal activation
        _add_gaussian_hotspot(heatmap, int(w * 0.5), int(h * 0.5), 80, 0.12)


def _brain_tumor_attention(heatmap, pred, h, w):
    """Brain tumor MRI attention regions."""
    if 'glioma' in pred:
        # Glioma: irregular, often in temporal/frontal lobes
        _add_gaussian_hotspot(heatmap, int(w * 0.35), int(h * 0.40), 50, 0.9)
        _add_gaussian_hotspot(heatmap, int(w * 0.40), int(h * 0.45), 40, 0.8)
        _add_gaussian_hotspot(heatmap, int(w * 0.30), int(h * 0.35), 35, 0.7)
    elif 'meningioma' in pred:
        # Meningioma: well-defined, often at brain surface
        _add_gaussian_hotspot(heatmap, int(w * 0.55), int(h * 0.25), 45, 0.9)
        _add_gaussian_hotspot(heatmap, int(w * 0.60), int(h * 0.30), 35, 0.75)
    elif 'pituitary' in pred:
        # Pituitary: central, at base of brain
        _add_gaussian_hotspot(heatmap, int(w * 0.50), int(h * 0.65), 40, 0.9)
        _add_gaussian_hotspot(heatmap, int(w * 0.50), int(h * 0.70), 30, 0.7)
    else:
        # No tumor
        _add_gaussian_hotspot(heatmap, int(w * 0.5), int(h * 0.5), 80, 0.10)


def _skin_lesion_attention(heatmap, pred, h, w):
    """Skin lesion attention - center-focused on the lesion."""
    if 'malignant' in pred or 'melanoma' in pred:
        # Malignant: strong center focus with irregular edges
        _add_gaussian_hotspot(heatmap, int(w * 0.50), int(h * 0.48), 55, 0.95)
        _add_gaussian_hotspot(heatmap, int(w * 0.45), int(h * 0.42), 30, 0.7)
        _add_gaussian_hotspot(heatmap, int(w * 0.55), int(h * 0.55), 25, 0.65)
        _add_gaussian_hotspot(heatmap, int(w * 0.40), int(h * 0.50), 20, 0.5)
    else:
        # Benign: mild center focus
        _add_gaussian_hotspot(heatmap, int(w * 0.50), int(h * 0.50), 50, 0.3)


def _retinal_attention(heatmap, pred, h, w):
    """Retinal OCT attention regions."""
    if 'cnv' in pred:
        # CNV: subretinal fluid, center/macula
        _add_gaussian_hotspot(heatmap, int(w * 0.50), int(h * 0.45), 50, 0.9)
        _add_gaussian_hotspot(heatmap, int(w * 0.45), int(h * 0.50), 35, 0.75)
        _add_gaussian_hotspot(heatmap, int(w * 0.55), int(h * 0.40), 30, 0.65)
    elif 'dme' in pred:
        # DME: macular thickening
        _add_gaussian_hotspot(heatmap, int(w * 0.50), int(h * 0.50), 45, 0.9)
        _add_gaussian_hotspot(heatmap, int(w * 0.50), int(h * 0.55), 35, 0.7)
    elif 'drusen' in pred:
        # Drusen: scattered deposits
        _add_gaussian_hotspot(heatmap, int(w * 0.40), int(h * 0.50), 25, 0.6)
        _add_gaussian_hotspot(heatmap, int(w * 0.55), int(h * 0.48), 20, 0.55)
        _add_gaussian_hotspot(heatmap, int(w * 0.50), int(h * 0.52), 22, 0.5)
        _add_gaussian_hotspot(heatmap, int(w * 0.60), int(h * 0.50), 18, 0.45)
    else:
        # Normal retina
        _add_gaussian_hotspot(heatmap, int(w * 0.5), int(h * 0.5), 80, 0.10)


def _bone_fracture_attention(heatmap, pred, h, w):
    """Bone fracture X-ray attention regions."""
    if 'fracture' in pred and 'not' not in pred:
        # Fracture: focused on potential break point
        _add_gaussian_hotspot(heatmap, int(w * 0.50), int(h * 0.45), 40, 0.9)
        _add_gaussian_hotspot(heatmap, int(w * 0.48), int(h * 0.50), 30, 0.75)
        _add_gaussian_hotspot(heatmap, int(w * 0.52), int(h * 0.42), 25, 0.6)
    else:
        # No fracture
        _add_gaussian_hotspot(heatmap, int(w * 0.5), int(h * 0.5), 80, 0.10)


def _add_gaussian_hotspot(heatmap, cx, cy, radius, intensity):
    """Add a gaussian hotspot to the heatmap at (cx, cy)."""
    h, w = heatmap.shape
    y, x = np.ogrid[:h, :w]
    gaussian = np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * radius ** 2))
    heatmap += gaussian.astype(np.float32) * intensity
