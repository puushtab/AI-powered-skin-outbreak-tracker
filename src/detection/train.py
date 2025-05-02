import os
import yaml
import argparse
import torch
from ultralytics import YOLO

def check_device():
    """Checks for available GPU and prints device information."""
    if torch.cuda.is_available():
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

    # Verify required subdirectories exist
    train_img_path = os.path.join(dataset_dir, 'train', 'images')
    val_img_path = os.path.join(dataset_dir, 'val', 'images')
    test_img_path = os.path.join(dataset_dir, 'test', 'images') 

    if not os.path.isdir(train_img_path):
        raise FileNotFoundError(f"Required directory not found: {train_img_path}")
    if not os.path.isdir(val_img_path):
         raise FileNotFoundError(f"Required directory not found: {val_img_path}")

    data_yaml = {
        'path': os.path.abspath(dataset_dir), # Root dataset directory
        'train': os.path.join('train', 'images'), 
        'val': os.path.join('val', 'images'),
        'nc': num_classes,
        'names': class_names
    }

    # Add test path only if the directory exists
    if os.path.isdir(test_img_path):
        data_yaml['test'] = os.path.join('test', 'images')
        print("Found 'test' directory, adding to data.yaml.")
    else:
        print("Optional 'test' directory not found, skipping in data.yaml.")


    try:
        with open(yaml_path, 'w') as f:
            yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)
        print(f"\nCreated data.yaml at: {yaml_path}")
        print("--- data.yaml Contents ---")
        print(yaml.dump(data_yaml))
        print("--------------------------")
        return yaml_path
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
    print(f"  Device: {device}")

    try:
        model = YOLO(model_name)

        results = model.train(
            data=data_yaml_path,
            epochs=epochs,
            imgsz=img_size,
            batch=batch_size,
            project=project_name,
            name=run_name,
            device=device if device else None,
            exist_ok=False
        )
        print("\n--- Training Finished Successfully ---")
        print(f"Results saved to: {results.save_dir}")
        best_weights_path = os.path.join(results.save_dir, 'weights', 'best.pt')
        if os.path.exists(best_weights_path):
            print(f"Best model weights: {best_weights_path}")
        else:
            print("Warning: 'best.pt' not found.")

    except Exception as e:
        print(f"\nAn error occurred during training: {e}")
        import traceback
        traceback.print_exc()
        raise SystemExit("Training failed.")


def main():
    parser = argparse.ArgumentParser(description="Train a YOLOv8 model skin anomaly detection.")
    # Removed --source-dir and --split-dir
    parser.add_argument('--dataset-dir', type=str, required=True, help='Path to the pre-split dataset directory (must contain train/ and val/ subdirs with images/ and labels/).')
    parser.add_argument('--class-names', nargs='+', required=True, help='List of class names in the correct order (e.g., --class-names anomaly mole lesion).')
    parser.add_argument('--model-name', type=str, default='yolov8s.pt', help='YOLOv8 model variant to train (e.g., yolov8n.pt, yolov8s.pt, yolov8s-seg.pt).')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs.')
    parser.add_argument('--batch-size', type=int, default=16, help='Training batch size.')
    parser.add_argument('--img-size', type=int, default=640, help='Image size for training (e.g., 640).')
    parser.add_argument('--project-name', type=str, default='YOLOv8_Training', help='Name for the main results directory.')
    parser.add_argument('--run-name', type=str, default='run_1', help='Specific name for this training run.')
    parser.add_argument('--device', type=str, default=None, help='Device to use (e.g., "cpu", "cuda:0", or None for auto-detect).')

    args = parser.parse_args()

    # Check device
    if args.device is None:
        args.device = check_device()
    else:
        print(f"Using specified device: {args.device}")

    # Verify dataset directory exists before proceeding
    if not os.path.isdir(args.dataset_dir):
         raise FileNotFoundError(f"Dataset directory not found: {args.dataset_dir}")

    # 1. Prepare data.yaml 
    data_yaml_path = prepare_data_yaml(args.dataset_dir, args.class_names)

    # 2. Train Model
    train_model(
        data_yaml_path,
        args.model_name,
        args.epochs,
        args.batch_size,
        args.img_size,
        args.project_name,
        args.run_name,
        args.device
    )

    print("\n--- Script Finished ---")

if __name__ == "__main__":
    main()