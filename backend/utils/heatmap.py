"""
MediScan AI - Heatmap Visualization Module
Generates Grad-CAM style heatmap overlays on medical images.
"""

import cv2
import numpy as np
import os


def generate_heatmap(image_path, prediction, output_path):
    """
    Generate a Grad-CAM style heatmap overlay on the medical image.
    Simulates attention regions based on the prediction type.
    
    Args:
        image_path: Path to the original scan image
        prediction: Predicted condition ('Normal', 'Pneumonia', 'Tuberculosis')
        output_path: Path to save the heatmap overlay image
    
    Returns:
        Path to the saved heatmap image
    """
    try:
        # Read the original image
        img = cv2.imread(image_path)
        if img is None:
            return None

        # Resize to standard dimensions
        img = cv2.resize(img, (512, 512))
        h, w = img.shape[:2]

        # Create a blank heatmap
        heatmap = np.zeros((h, w), dtype=np.float32)

        # Generate attention regions based on prediction
        if prediction == 'Pneumonia':
            # Pneumonia typically shows in lower lung regions
            # Create multiple hotspots in lung areas
            _add_gaussian_hotspot(heatmap, int(w * 0.35), int(h * 0.55), 60, 0.9)
            _add_gaussian_hotspot(heatmap, int(w * 0.65), int(h * 0.50), 55, 0.85)
            _add_gaussian_hotspot(heatmap, int(w * 0.40), int(h * 0.65), 45, 0.7)
            _add_gaussian_hotspot(heatmap, int(w * 0.60), int(h * 0.60), 50, 0.75)

        elif prediction == 'Tuberculosis':
            # TB typically shows in upper lung regions
            _add_gaussian_hotspot(heatmap, int(w * 0.35), int(h * 0.30), 55, 0.95)
            _add_gaussian_hotspot(heatmap, int(w * 0.60), int(h * 0.35), 50, 0.8)
            _add_gaussian_hotspot(heatmap, int(w * 0.45), int(h * 0.25), 40, 0.7)
            _add_gaussian_hotspot(heatmap, int(w * 0.30), int(h * 0.40), 35, 0.6)

        else:
            # Normal - minimal/no activation
            _add_gaussian_hotspot(heatmap, int(w * 0.5), int(h * 0.5), 80, 0.15)

        # Normalize heatmap to 0-255
        heatmap = np.clip(heatmap, 0, 1)
        heatmap_uint8 = np.uint8(255 * heatmap)

        # Apply color map (JET for medical visualization)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        # Overlay heatmap on original image
        overlay = cv2.addWeighted(img, 0.6, heatmap_colored, 0.4, 0)

        # Add prediction label
        label = f"Prediction: {prediction}"
        cv2.putText(overlay, label, (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Save the heatmap overlay
        cv2.imwrite(output_path, overlay)
        return output_path

    except Exception as e:
        print(f"[Heatmap Error] {e}")
        return None


def _add_gaussian_hotspot(heatmap, cx, cy, radius, intensity):
    """Add a gaussian hotspot to the heatmap at (cx, cy)."""
    h, w = heatmap.shape
    y, x = np.ogrid[:h, :w]
    gaussian = np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * radius ** 2))
    heatmap += gaussian.astype(np.float32) * intensity
