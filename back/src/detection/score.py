import os
# No argparse needed
import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
import traceback
from scipy.ndimage import gaussian_filter
from ultralytics import YOLO


MODEL_WEIGHTS_PATH = r'best.pt'     
TEST_IMAGE_PATH = r'final_test.jpg' 
CONFIDENCE_THRESHOLD = 0.3                    
OUTPUT_PATH = r'output.jpg' 
NO_DISPLAY = False                               


SEVERITY_SCORE_MAP = {
    'Acne': 5,
    'Pigmentation': 4,
    'Blackheads': 2,
    'Excess sebum': 2,
    'Enlarged Pores': 1,
}
DEFAULT_SEVERITY_SCORE = 1

# Heatmap settings
HEATMAP_WEIGHTING = 'confidence' # 'severity' or 'confidence'
HEATMAP_ALPHA = 0.5            # Heatmap transparency
COLORMAP = cv2.COLORMAP_JET    # OpenCV colormap
GAUSSIAN_SPREAD_SIGMA = 40     # Controls heatmap spread radius 
SECONDARY_BLUR_KERNEL_SIZE = 0 # Optional secondary blur (0 to disable)

# Score calculation weights
AREA_WEIGHT = 0.3
INTENSITY_WEIGHT = 0.6
SCORE_RANGE = (0, 100)
# --- End Configuration ---


# --- Function Definitions ---

def generate_spread_heatmap(image, detection_results, severity_map, default_s_i, weighting=HEATMAP_WEIGHTING, alpha=HEATMAP_ALPHA, spread_sigma=GAUSSIAN_SPREAD_SIGMA, secondary_blur_ksize=SECONDARY_BLUR_KERNEL_SIZE, colormap=COLORMAP):
    """Generates a heatmap overlay where detection influence spreads via Gaussians."""
    if not isinstance(image, np.ndarray) or image.ndim != 3: return image, np.zeros(image.shape[:2] if isinstance(image, np.ndarray) else (100, 100), dtype=np.float32)
    if not detection_results or len(detection_results) == 0: return image, np.zeros(image.shape[:2], dtype=np.float32)

    try:
        result = detection_results[0]
        boxes = result.boxes
        names = getattr(result, 'names', {});
        if not isinstance(names, dict): names = {}
        img_h, img_w = image.shape[:2]
    except (AttributeError, IndexError) as e: return image, np.zeros(image.shape[:2], dtype=np.float32)

    heatmap_raw = np.zeros((img_h, img_w), dtype=np.float32)
    num_detections = len(boxes) if boxes is not None else 0

    if num_detections > 0:
        points_data = []
        for box in boxes:
             try:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx = max(0, min(img_w - 1, int((x1 + x2) / 2)))
                cy = max(0, min(img_h - 1, int((y1 + y2) / 2)))
                point_weight = 1.0
                if weighting == 'severity':
                    class_id = int(box.cls[0])
                    class_name = names.get(class_id, f"class_{class_id}")
                    s_i = severity_map.get(class_name, default_s_i)
                    point_weight = float(s_i)
                elif weighting == 'confidence':
                    point_weight = float(box.conf[0])
                if point_weight > 0:
                    points_data.append((cy, cx, point_weight))
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


def calculate_facial_severity_v2(detection_results, image_shape, severity_map, default_s_i, score_range=SCORE_RANGE, area_weight=AREA_WEIGHT, intensity_weight=INTENSITY_WEIGHT):
    """Calculates a facial severity score based on affected area and intensity."""
    if not detection_results or len(detection_results) == 0: return score_range[0], 0.0, 0.0, 0
    if not isinstance(image_shape, tuple) or len(image_shape) < 2: return score_range[0], 0.0, 0.0, 0

    try:
        result = detection_results[0]
        boxes = result.boxes
        names = getattr(result, 'names', {});
        if not isinstance(names, dict): names = {}
        img_h, img_w = image_shape[:2]; total_image_area = float(img_h * img_w)
    except (AttributeError, IndexError) as e: return score_range[0], 0.0, 0.0, 0

    N = len(boxes) if boxes is not None else 0
    if N == 0 or total_image_area <= 0: return score_range[0], 0.0, 0.0, 0

    total_lesion_area = 0.0; sum_severity_points = 0.0; valid_detections = 0
    for box in boxes:
         try:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy(); w = x2 - x1; h = y2 - y1
            if w <=0 or h <= 0: continue
            a_i = float(w * h); total_lesion_area += a_i
            class_id = int(box.cls[0]); class_name = names.get(class_id, f"class_{class_id}")
            s_i = severity_map.get(class_name, default_s_i); sum_severity_points += s_i
            valid_detections += 1
         except (AttributeError, IndexError, TypeError) as e: continue

    N = valid_detections
    if N == 0: return score_range[0], 0.0, 0.0, 0

    percentage_affected_area = (total_lesion_area / total_image_area) * 100.0
    average_intensity = sum_severity_points / N if N > 0 else 0.0

    max_expected_area_percent = 50.0
    scaled_area_component = min(1.0, percentage_affected_area / max_expected_area_percent) * (score_range[1] - score_range[0])
    max_possible_avg_intensity = max(severity_map.values()) if severity_map else default_s_i
    if max_possible_avg_intensity <= 0: max_possible_avg_intensity = 5.0
    scaled_intensity_component = min(1.0, average_intensity / max_possible_avg_intensity) * (score_range[1] - score_range[0])

    final_score = (area_weight * scaled_area_component) + (intensity_weight * scaled_intensity_component) + score_range[0]
    final_score = max(score_range[0], min(score_range[1], final_score))
    return final_score, percentage_affected_area, average_intensity, N

def analyze_skin_image(model_path, image_path,
                       conf_threshold=CONFIDENCE_THRESHOLD,
                       severity_map=SEVERITY_SCORE_MAP,
                       default_severity=DEFAULT_SEVERITY_SCORE,
                       heatmap_alpha=HEATMAP_ALPHA,
                       heatmap_sigma=GAUSSIAN_SPREAD_SIGMA,
                       area_weight=AREA_WEIGHT,
                       intensity_weight=INTENSITY_WEIGHT,
                       score_range=SCORE_RANGE):
    """
    Loads a model, predicts on an image, calculates severity score,
    generates a heatmap, and returns the results.

    Args:
        model_path (str): Path to the trained YOLOv8 model (.pt file).
        image_path (str): Path to the input image file.
        conf_threshold (float): Confidence threshold for detection.
        severity_map (dict): Mapping of class names to severity scores.
        default_severity (int/float): Default severity score for unmapped classes.
        heatmap_alpha (float): Transparency for the heatmap overlay.
        heatmap_sigma (float): Sigma value for Gaussian spread heatmap.
        area_weight (float): Weight for area component in score calculation.
        intensity_weight (float): Weight for intensity component in score calculation.
        score_range (tuple): Min and max possible score (e.g., (0, 100)).

    Returns:
        dict: A dictionary containing results:
              'success' (bool): True if analysis completed, False otherwise.
              'message' (str): Status message or error description.
              'severity_score' (float): Calculated overall severity score.
              'percentage_area' (float): Percentage of image area covered by detections.
              'average_intensity' (float): Average severity score of detected items.
              'lesion_count' (int): Number of valid lesions detected and scored.
              'original_image_bgr' (np.ndarray): Original image loaded (BGR).
              'heatmap_overlay_bgr' (np.ndarray): Image with heatmap overlay (BGR).
              'detections' (list): List of detected objects (class_name, confidence).
              'model_classes' (dict): Class mapping from the loaded model.
              Returns None if critical errors occur (e.g., file not found).
    """
    results = {
        'success': False, 'message': 'Analysis not started.',
        'severity_score': score_range[0], 'percentage_area': 0.0,
        'average_intensity': 0.0, 'lesion_count': 0,
        'original_image_bgr': None, 'heatmap_overlay_bgr': None,
        'detections': [], 'model_classes': {}
    }

    # --- Validate Inputs ---
    if not os.path.exists(model_path):
        results['message'] = f"Model file not found: {model_path}"
        return results
    if not os.path.exists(image_path):
        results['message'] = f"Image file not found: {image_path}"
        return results

    try:
        # --- Load Model ---
        print(f"--- Loading Model: {model_path} ---")
        model = YOLO(model_path)
        results['model_classes'] = getattr(model, 'names', {})
        if not isinstance(results['model_classes'], dict): results['model_classes'] = {}
        print(f"Model loaded. Classes: {results['model_classes']}")

        # --- Read Image ---
        print(f"\n--- Reading Image: {image_path} ---")
        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
            results['message'] = f"Could not read image file: {image_path}"
            return results
        results['original_image_bgr'] = image_bgr.copy() # Store original
        original_shape = image_bgr.shape
        print(f"Image shape: {original_shape}")

        # --- Run Prediction ---
        print(f"\n--- Running Prediction (Confidence: {conf_threshold}) ---")
        predict_results = model.predict(source=image_path, conf=conf_threshold, save=False)

        # --- Calculate Score ---
        print("\n--- Calculating Severity Score ---")
        score, perc_a, avg_i, n_lesions = calculate_facial_severity_v2(
            predict_results, original_shape, severity_map, default_severity,
            score_range=score_range, area_weight=area_weight, intensity_weight=intensity_weight
        )
        results.update({
            'severity_score': score, 'percentage_area': perc_a,
            'average_intensity': avg_i, 'lesion_count': n_lesions
        })
        print(f"Score calculated: {score:.2f}")

        # --- Generate Heatmap ---
        print(f"\n--- Generating Heatmap (Sigma: {heatmap_sigma}, Alpha: {heatmap_alpha}) ---")
        heatmap_overlay, _ = generate_spread_heatmap(
            image_bgr, predict_results, severity_map, default_severity,
            alpha=heatmap_alpha, spread_sigma=heatmap_sigma
            # Pass other heatmap params if needed
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
                except (AttributeError, IndexError, TypeError): continue # Skip problematic box

        results['success'] = True
        results['message'] = 'Analysis completed successfully.'

    except (FileNotFoundError, IOError) as e:
        results['message'] = f"File Error: {e}"
        print(f"ERROR: {results['message']}")
    except ImportError as e:
         results['message'] = f"Import Error: Missing library. {e}."
         print(f"ERROR: {results['message']}")
    except Exception as e:
        results['message'] = f"An unexpected error occurred: {e}"
        print(f"\nERROR: {results['message']}")
        traceback.print_exc()

    return results

def main():
    """Main function to run scoring and heatmap generation with hardcoded settings."""

    # --- Use Configuration Constants ---
    model_path = MODEL_WEIGHTS_PATH
    image_path = TEST_IMAGE_PATH
    conf_threshold = CONFIDENCE_THRESHOLD
    output_path = OUTPUT_PATH
    no_display = NO_DISPLAY
    sigma = GAUSSIAN_SPREAD_SIGMA
    alpha = HEATMAP_ALPHA
    # --- End Using Constants ---

    if not os.path.exists(model_path): print(f"ERROR: Model weights not found at: {model_path}"); raise SystemExit(1)
    if not os.path.exists(image_path): print(f"ERROR: Input image not found at: {image_path}"); raise SystemExit(1)

    try:
        print(f"--- Loading Model: {model_path} ---")
        model = YOLO(model_path)
        print(f"Model loaded. Classes: {model.names}")

        print(f"\n--- Reading Image: {image_path} ---")
        image_bgr = cv2.imread(image_path)
        if image_bgr is None: raise IOError(f"Could not read image file: {image_path}")
        original_shape = image_bgr.shape
        print(f"Image shape: {original_shape}")

        print(f"\n--- Running Prediction (Confidence: {conf_threshold}) ---")
        predict_results = model.predict(source=image_path, conf=conf_threshold, save=False)

        print("\n--- Calculating Severity Score ---")
        severity_score, perc_area, avg_intensity, num_lesions = calculate_facial_severity_v2(
            predict_results, original_shape, SEVERITY_SCORE_MAP, DEFAULT_SEVERITY_SCORE,
            score_range=SCORE_RANGE, area_weight=AREA_WEIGHT, intensity_weight=INTENSITY_WEIGHT
        )
        print(f"-----------------------------------")
        print(f" Facial Severity Score: {severity_score:.2f} / {SCORE_RANGE[1]}")
        print(f" Affected Area (%):     {perc_area:.2f}%")
        print(f" Average Intensity (s_i): {avg_intensity:.2f}")
        print(f" Number of Lesions (N): {num_lesions}")
        print(f"-----------------------------------")

        print(f"\n--- Generating Heatmap (Sigma: {sigma}, Alpha: {alpha}) ---")
        image_with_heatmap, _ = generate_spread_heatmap(
            image_bgr.copy(), predict_results, SEVERITY_SCORE_MAP, DEFAULT_SEVERITY_SCORE,
            weighting=HEATMAP_WEIGHTING, alpha=alpha,
            spread_sigma=sigma,
            secondary_blur_ksize=SECONDARY_BLUR_KERNEL_SIZE, colormap=COLORMAP
        )

        output_filename = None
        if output_path:
            try:
                output_dir = os.path.dirname(output_path)
                if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)
                success = cv2.imwrite(output_path, image_with_heatmap)
                if success: print(f"Output image saved to: {output_path}"); output_filename = os.path.basename(output_path)
                else: print(f"ERROR: Failed to save output image to {output_path}")
            except Exception as e: print(f"ERROR saving output image: {e}")

        if not no_display:
            print("\n--- Displaying Results ---")
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            heatmap_overlay_rgb = cv2.cvtColor(image_with_heatmap, cv2.COLOR_BGR2RGB)
            fig, axes = plt.subplots(1, 2, figsize=(16, 8)); fig.suptitle(f"Analysis for: {os.path.basename(image_path)}", fontsize=16)
            axes[0].imshow(image_rgb); axes[0].set_title('Original Image'); axes[0].axis('off')
            title_str = f'Severity Heatmap (Score: {severity_score:.1f}, Sigma: {sigma})';
            if output_filename: title_str += f'\nSaved as: {output_filename}'
            axes[1].imshow(heatmap_overlay_rgb); axes[1].set_title(title_str); axes[1].axis('off')
            plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()

        if predict_results and len(predict_results) > 0 and hasattr(predict_results[0], 'boxes') and len(predict_results[0].boxes) > 0:
            print(f"\n--- Detected Objects ({len(predict_results[0].boxes)}) ---")
            names_map = getattr(model, 'names', {});
            if not isinstance(names_map, dict): names_map = {}
            for box in predict_results[0].boxes:
                try:
                    class_id = int(box.cls[0]); confidence = float(box.conf[0])
                    class_name = names_map.get(class_id, f"class_{class_id}")
                    print(f"  - Class: {class_name} ({class_id}), Confidence: {confidence:.3f}")
                except (AttributeError, IndexError, TypeError) as e: print(f"  - Error accessing details for one box: {e}")
        elif predict_results and len(predict_results) > 0: print("\nNo objects detected with confidence above the threshold.")

        print("\n--- Scoring Script Finished ---")

    except (FileNotFoundError, IOError) as e: print(f"ERROR: {e}"); raise SystemExit(1)
    except ImportError as e: print(f"ERROR: Missing library. {e}. Please install required libraries."); raise SystemExit(1)
    except Exception as e: print(f"\nAn unexpected error occurred: {e}"); traceback.print_exc(); raise SystemExit(1)


if __name__ == "__main__":
    main()