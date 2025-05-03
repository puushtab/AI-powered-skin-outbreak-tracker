import os
import yaml
import torch
from ultralytics import YOLO

#--- Configuration ---
DATASET_DIR = '/content/Skin-Issue-Detection-1' 
CLASS_NAMES = ['Acne', 'Pigmentation', 'Blackheads', 'Excess sebum', 'Enlarged Pores'] 
MODEL_NAME = 'yolov8s.pt'       
EPOCHS = 75                     
BATCH_SIZE = 8                  
IMG_SIZE = 640                  
PROJECT_NAME = 'Skin_Condition_Training' 
RUN_NAME = 'yolov8s_75e_b8_hardcoded' 
DEVICE = None                   
# --- End Configuration ---


def check_device(requested_device=None):
    """Checks for available GPU and selects the device."""
    if requested_device:
        if requested_device.startswith("cuda") and not torch.cuda.is_available():
            print(f"Warning: Requested device '{requested_device}' but CUDA not available. Falling back to CPU.")
            device = torch.device("cpu")
            print("Using CPU.")
            return "cpu"
        else:
            device = torch.device(requested_device)
            print(f"Using specified device: {requested_device}")
            return requested_device
    elif torch.cuda.is_available():
        device = torch.device("cuda:0")
        print("GPU is available.")
        print(f"Device: {torch.cuda.get_device_name(0)}")
        return "cuda:0"
    else:
        device = torch.device("cpu")
        print("GPU not available, using CPU.")
        return "cpu"

def prepare_data_yaml(dataset_dir, class_names):
    """Creates the data.yaml file pointing to the pre-split dataset."""
    num_classes = len(class_names)
    yaml_path = os.path.join(dataset_dir, 'data.yaml')

    train_img_path = os.path.join(dataset_dir, 'train', 'images')
    val_img_path = os.path.join(dataset_dir, 'val', 'images')
    test_img_path = os.path.join(dataset_dir, 'test', 'images')

    if not os.path.isdir(train_img_path): raise FileNotFoundError(f"Required directory not found: {train_img_path}")
    if not os.path.isdir(val_img_path): raise FileNotFoundError(f"Required directory not found: {val_img_path}")

    data_yaml = {
        'path': os.path.abspath(dataset_dir),
        'train': os.path.join('train', 'images'),
        'val': os.path.join('val', 'images'),
        'nc': num_classes,
        'names': class_names
    }
    if os.path.isdir(test_img_path): data_yaml['test'] = os.path.join('test', 'images')

    try:
        with open(yaml_path, 'w') as f: yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)
        print(f"\nCreated data.yaml at: {yaml_path}")
    except Exception as e:
        print(f"Error writing data.yaml file: {e}")
        raise SystemExit("Failed to create data.yaml")

def train_model(data_yaml_path, model_name, epochs, batch_size, img_size, project_name, run_name, device):
    """Loads and trains the YOLOv8 model."""
    print("\n--- Starting YOLOv8 Training ---")
    print(f"  Model: {model_name}")
    print(f"  Dataset YAML: {data_yaml_path}")
    print(f"  Epochs: {epochs}")
    print(f"  Image Size: {img_size}")
    print(f"  Batch Size: {batch_size}")
    print(f"  Project: {project_name}")
    print(f"  Run Name: {run_name}")
    print(f"  Device: {device if device else 'Auto-Detect'}")

    try:
        model = YOLO(model_name)
        results = model.train(
            data=data_yaml_path, epochs=epochs, imgsz=img_size, batch=batch_size,
            project=project_name, name=run_name, device=device, exist_ok=False
        )
        print("\n--- Training Finished Successfully ---")
        print(f"Results saved to: {results.save_dir}")
        best_weights_path = os.path.join(results.save_dir, 'weights', 'best.pt')
        if os.path.exists(best_weights_path): print(f"Best model weights: {best_weights_path}")
        else: print("Warning: 'best.pt' not found.")
    except Exception as e:
        print(f"\nAn error occurred during training: {e}")
        import traceback; traceback.print_exc()
        raise SystemExit("Training failed.")


def main():
    """Main function to run the training process with hardcoded settings."""


    dataset_dir = DATASET_DIR
    class_names = CLASS_NAMES
    model_name = MODEL_NAME
    epochs = EPOCHS
    batch_size = BATCH_SIZE
    img_size = IMG_SIZE
    project_name = PROJECT_NAME
    run_name = RUN_NAME
    device_to_use = DEVICE


    # Check device
    selected_device = check_device(device_to_use)

    # Verify dataset directory exists
    if not os.path.isdir(dataset_dir):
         raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    # 1. Prepare data.yaml
    data_yaml_path = prepare_data_yaml(dataset_dir, class_names)

    # 2. Train Model
    train_model(
        data_yaml_path,
        model_name,
        epochs,
        batch_size,
        img_size,
        project_name,
        run_name,
        selected_device 
    )

    print("\n--- Script Finished ---")

if __name__ == "__main__":
    main()