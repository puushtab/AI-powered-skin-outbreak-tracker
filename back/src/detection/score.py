import os
import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt 
import math 
import traceback
from scipy.ndimage import gaussian_filter
from ultralytics import YOLO
import base64 

# --- Default Configuration Constants ---
DEFAULT_SEVERITY_SCORE_MAP = {
    'whiteheads': 1,     # Mild, non-inflammatory
    'blackheads': 1,     # Mild, non-inflammatory
    'papules': 3,        # Mild to moderate, inflammatory
    'pustules': 4,       # Moderate, inflammatory (contains pus)
    'nodules': 5,        # Severe, deep and painful
    'dark spot': 2       # Post-inflammatory hyperpigmentation (not active acne)
}
DEFAULT_SEVERITY_SCORE = 1
DEFAULT_HEATMAP_WEIGHTING = 'confidence'
DEFAULT_HEATMAP_ALPHA = 0.5
DEFAULT_COLORMAP = cv2.COLORMAP_JET
DEFAULT_GAUSSIAN_SPREAD_SIGMA = 90
DEFAULT_SECONDARY_BLUR_KERNEL_SIZE = 0
DEFAULT_SCORE_RANGE = (0, 100) # AcneAI score range
DEFAULT_CONFIDENCE_THRESHOLD = 0.25

# --- Helper Function Definitions ---

def generate_spread_heatmap(image, detection_results, severity_map, default_s_i,
                            weighting=DEFAULT_HEATMAP_WEIGHTING, alpha=DEFAULT_HEATMAP_ALPHA,
                            spread_sigma=DEFAULT_GAUSSIAN_SPREAD_SIGMA,
                            secondary_blur_ksize=DEFAULT_SECONDARY_BLUR_KERNEL_SIZE,
                            colormap=DEFAULT_COLORMAP):
    """Generates a heatmap overlay. (Function body remains the same)"""
    if not isinstance(image, np.ndarray) or image.ndim != 3: return image, np.zeros(image.shape[:2] if isinstance(image, np.ndarray) else (100, 100), dtype=np.float32)
    if not detection_results or len(detection_results) == 0: return image, np.zeros(image.shape[:2], dtype=np.float32)
    try:
        result = detection_results[0]; boxes = result.boxes; names = getattr(result, 'names', {});
        if not isinstance(names, dict): names = {}
        img_h, img_w = image.shape[:2]
    except (AttributeError, IndexError) as e: return image, np.zeros(image.shape[:2], dtype=np.float32)
    heatmap_raw = np.zeros((img_h, img_w), dtype=np.float32); num_detections = len(boxes) if boxes is not None else 0
    if num_detections > 0:
        points_data = []
        for box in boxes:
             try:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy(); cx = max(0, min(img_w - 1, int((x1 + x2) / 2))); cy = max(0, min(img_h - 1, int((y1 + y2) / 2)))
                point_weight = 1.0
                if weighting == 'severity':
                    class_id = int(box.cls[0]); class_name = names.get(class_id, f"class_{class_id}"); s_i = severity_map.get(class_name, default_s_i); point_weight = float(s_i)
                elif weighting == 'confidence': point_weight = float(box.conf[0])
                if point_weight > 0: points_data.append((cy, cx, point_weight))
             except (AttributeError, IndexError, TypeError) as e: continue
        if points_data:
            for y, x, weight in points_data: heatmap_raw[y, x] += weight
            if spread_sigma > 0: heatmap_spread = gaussian_filter(heatmap_raw, sigma=spread_sigma)
            else: heatmap_spread = heatmap_raw
            if secondary_blur_ksize and secondary_blur_ksize > 1 and secondary_blur_ksize % 2 == 1: heatmap_blurred = cv2.GaussianBlur(heatmap_spread, (secondary_blur_ksize, secondary_blur_ksize), 0)
            else: heatmap_blurred = heatmap_spread
            max_val = np.max(heatmap_blurred)
            if max_val > 1e-6: heatmap_norm = cv2.normalize(heatmap_blurred, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            else: heatmap_norm = np.zeros(heatmap_blurred.shape, dtype=cv2.CV_8U)
            heatmap_color = cv2.applyColorMap(heatmap_norm, colormap)
            image_uint8 = image.astype(np.uint8) if image.dtype != np.uint8 else image
            heatmap_overlay = cv2.addWeighted(heatmap_color, alpha, image_uint8, 1 - alpha, 0)
            return heatmap_overlay, heatmap_norm
        else: return image, heatmap_raw
    else: return image, heatmap_raw


def calculate_acneai_score(detection_results, image_shape, severity_map, default_s_i):
    """
    Calculates score based on AcneAI paper (Eq 3). (Function body remains the same)
    Returns: score_S, percentage_affected_area, average_intensity, N
    """
    score_range=(0, 100)
    if not detection_results or len(detection_results) == 0: return score_range[0], 0.0, 0.0, 0
    if not isinstance(image_shape, tuple) or len(image_shape) < 2: return score_range[0], 0.0, 0.0, 0
    try:
        result = detection_results[0]; boxes = result.boxes; names = getattr(result, 'names', {});
        if not isinstance(names, dict): names = {}
        img_h, img_w = image_shape[:2]; A = float(img_h * img_w)
    except (AttributeError, IndexError) as e: return score_range[0], 0.0, 0.0, 0
    N_total_boxes = len(boxes) if boxes is not None else 0
    if N_total_boxes == 0 or A <= 0: return score_range[0], 0.0, 0.0, 0
    sum_term = 0.0; total_lesion_area = 0.0; sum_severity_points = 0.0; valid_detections = 0
    for box in boxes:
         try:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy(); w = x2 - x1; h = y2 - y1
            if w <= 0 or h <= 0: continue
            a_i = float(w * h); total_lesion_area += a_i
            class_id = int(box.cls[0]); class_name = names.get(class_id, f"class_{class_id}")
            s_i = severity_map.get(class_name, default_s_i); sum_severity_points += s_i
            sum_term += (s_i * a_i) / A; valid_detections += 1
         except (AttributeError, IndexError, TypeError) as e: continue
    N = valid_detections
    if N == 0: return score_range[0], 0.0, 0.0, 0
    try:
        inner_term = 20.0 * sum_term; score_S = (200.0 / math.pi) * math.atan(inner_term)
    except Exception as e: print(f"Error during score math calc: {e}"); score_S = score_range[0]
    score_S = max(score_range[0], min(score_range[1], score_S))
    percentage_affected_area = (total_lesion_area / A) * 100.0
    average_intensity = sum_severity_points / N if N > 0 else 0.0
    return score_S, percentage_affected_area, average_intensity, N


# --- Main Analysis Function ---
def analyze_skin_image(model_path, image_path,
                       conf_threshold=DEFAULT_CONFIDENCE_THRESHOLD,
                       severity_map=DEFAULT_SEVERITY_SCORE_MAP,
                       default_severity=DEFAULT_SEVERITY_SCORE,
                       heatmap_alpha=DEFAULT_HEATMAP_ALPHA,
                       heatmap_sigma=DEFAULT_GAUSSIAN_SPREAD_SIGMA
                       # Add other heatmap/score params as needed
                       ):
    """
    Loads a model, predicts on an image, calculates severity score using AcneAI
    formula, generates a heatmap, and returns the results.

    Args:
        model_path (str): Path to the trained YOLOv8 model (.pt file).
        image_path (str): Path to the input image file.
        conf_threshold (float): Confidence threshold for detection.
        severity_map (dict): Mapping of class names to severity scores (s_i for AcneAI).
        default_severity (int/float): Default severity score (s_i) for unmapped classes.
        heatmap_alpha (float): Transparency for the heatmap overlay.
        heatmap_sigma (float): Sigma value for Gaussian spread heatmap.

    Returns:
        dict: A dictionary containing results:
              'success' (bool): True if analysis completed, False otherwise.
              'message' (str): Status message or error description.
              'severity_score' (float): Calculated AcneAI severity score (S).
              'percentage_area' (float): Info: Percentage of image area covered by detections.
              'average_intensity' (float): Info: Average severity score (s_i) of detected items.
         y     'lesion_count' (int): Info: Number of valid lesions detected and used in score.
              'original_image_bgr' (np.ndarray): Original image loaded (BGR).
              'heatmap_overlay_bgr' (np.ndarray): Image with heatmap overlay (BGR).
              'detections' (list): List of detected objects (class_name, confidence).
              'model_classes' (dict): Class mapping from the loaded model.
    """
    # Initialize results dictionary
    results = {
        'success': False, 'message': 'Analysis not started.',
        'severity_score': 0.0, 'percentage_area': 0.0, # Initialize with defaults
        'average_intensity': 0.0, 'lesion_count': 0,
        'original_image_bgr': None, 'heatmap_overlay_bgr': None,
        'detections': [], 'model_classes': {}
    }

    # --- Validate Inputs ---
    if not os.path.exists(model_path): results['message'] = f"Model file not found: {model_path}"; return results
    if not os.path.exists(image_path): results['message'] = f"Image file not found: {image_path}"; return results

    try:
        # --- Load Model ---
        print(f"--- Loading Model: {model_path} ---")
        model = YOLO(model_path)
        results['model_classes'] = getattr(model, 'names', {});
        if not isinstance(results['model_classes'], dict): results['model_classes'] = {}
        print(f"Model loaded. Classes: {results['model_classes']}")

        # --- Read Image ---
        print(f"\n--- Reading Image: {image_path} ---")
        image_bgr = cv2.imread(image_path)
        if image_bgr is None: raise IOError(f"Could not read image file: {image_path}")
        results['original_image_bgr'] = image_bgr.copy()
        original_shape = image_bgr.shape
        print(f"Image shape: {original_shape}")

        # --- Run Prediction ---
        print(f"\n--- Running Prediction (Confidence: {conf_threshold}) ---")
        predict_results = model.predict(source=image_path, conf=conf_threshold, save=False)

        # --- Calculate Score using AcneAI Formula ---
        print("\n--- Calculating Severity Score (AcneAI Formula) ---")
        # Call the correct scoring function
        score, perc_a, avg_i, n_lesions = calculate_acneai_score(
            predict_results,
            original_shape,
            severity_map,
            default_severity
        )
        # Store results in the dictionary
        results.update({
            'severity_score': score, # Store AcneAI score under the standard key
            'percentage_area': perc_a,
            'average_intensity': avg_i,
            'lesion_count': n_lesions
        })
        print(f"Score calculated: {score:.2f}")

        # --- Generate Heatmap ---
        print(f"\n--- Generating Heatmap (Sigma: {heatmap_sigma}, Alpha: {heatmap_alpha}) ---")
        heatmap_overlay, _ = generate_spread_heatmap(
            image_bgr, # Use original BGR for blending
            predict_results,
            severity_map, # Use the same map for heatmap intensity weighting
            default_severity,
            alpha=heatmap_alpha,
            spread_sigma=heatmap_sigma
            # Add other heatmap params if needed (e.g., weighting='severity')
        )
        results['heatmap_overlay_bgr'] = heatmap_overlay
        print("Heatmap generated.")

        # --- Extract Detections ---
        if predict_results and len(predict_results) > 0 and hasattr(predict_results[0], 'boxes') and len(predict_results[0].boxes) > 0:
            names_map = results['model_classes']
            for box in predict_results[0].boxes:
                try:
                    class_id = int(box.cls[0]); confidence = float(box.conf[0])
                    class_name = names_map.get(class_id, f"class_{class_id}")
                    results['detections'].append({'class_name': class_name, 'confidence': confidence})
                except (AttributeError, IndexError, TypeError): continue

        results['success'] = True
        results['message'] = 'Analysis completed successfully using AcneAI score formula.'

    except (FileNotFoundError, IOError) as e: results['message'] = f"File Error: {e}"; print(f"ERROR: {results['message']}")
    except ImportError as e: results['message'] = f"Import Error: Missing library. {e}."; print(f"ERROR: {results['message']}")
    except Exception as e: results['message'] = f"An unexpected error occurred: {e}"; print(f"\nERROR: {results['message']}"); traceback.print_exc()

    return results


# --- Example Usage ---
if __name__ == "__main__":
    print("--- Running Scoring Script Example (using AcneAI score) ---")

    # Define Inputs for the Example
    example_model_path = 'best.pt' 
    example_image_path = 'final_test.jpg' 
    example_output_path = './acneai_analysis_output.png' 
    display_results = True

    # Call the updated Analysis Function
    analysis_results = analyze_skin_image(
        model_path=example_model_path,
   heatmap_sigma=DEFAULT_GAUSSIAN_SPREAD_SIGMA
    )

    # Process the Results
    if analysis_results and analysis_results['success']:
        print("\n--- Analysis Results ---")
        print(f" AcneAI Severity Score: {analysis_results['severity_score']:.2f}")
        print(f" Info - Affected Area (%): {analysis_results['percentage_area']:.2f}%")
        print(f" Info - Average Intensity: {analysis_results['average_intensity']:.2f}")
        print(f" Info - Lesion Count Used: {analysis_results['lesion_count']}")
        print(f" Detections ({len(analysis_results['detections'])}):")
        for det in analysis_results['detections']: print(f"  - Class: {det['class_name']}, Conf: {det['confidence']:.3f}")

        # Handle Output Image Saving
        output_filename = None
        if example_output_path and analysis_results['heatmap_overlay_bgr'] is not None:
            try:
                output_dir = os.path.dirname(example_output_path);
                if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)
                success = cv2.imwrite(example_output_path, analysis_results['heatmap_overlay_bgr'])
                if success: print(f"\nOutput image saved to: {example_output_path}"); output_filename = os.path.basename(example_output_path)
                else: print(f"\nERROR: Failed to save output image to {example_output_path}")
            except Exception as e: print(f"\nERROR saving output image: {e}")

        # Handle Display
        if display_results and analysis_results['original_image_bgr'] is not None and analysis_results['heatmap_overlay_bgr'] is not None:
            print("\n--- Displaying Results ---")
            image_rgb = cv2.cvtColor(analysis_results['original_image_bgr'], cv2.COLOR_BGR2RGB)
            heatmap_overlay_rgb = cv2.cvtColor(analysis_results['heatmap_overlay_bgr'], cv2.COLOR_BGR2RGB)
            fig, axes = plt.subplots(1, 2, figsize=(16, 8)); fig.suptitle(f"Analysis for: {os.path.basename(example_image_path)}", fontsize=16)
            axes[0].imshow(image_rgb); axes[0].set_title('Original Image'); axes[0].axis('off')
            # Update title to reflect AcneAI score
            title_str = f'Severity Heatmap (AcneAI Score: {analysis_results["severity_score"]:.1f})';
            if output_filename: title_str += f'\nSaved as: {output_filename}'
            axes[1].imshow(heatmap_overlay_rgb); axes[1].set_title(title_str); axes[1].axis('off')
            plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()
    else:
        print(f"\nAnalysis failed: {analysis_results.get('message', 'Unknown error') if analysis_results else 'Function returned None'}")

    print("\n--- Scoring Script Example Finished ---")
