"""
Helper Utilities
General purpose helper functions used across the application.
"""
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import cv2
import numpy as np


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate unique filename using timestamp and UUID.
    
    Args:
        original_filename: Original uploaded filename
        
    Returns:
        Unique filename with original extension
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    extension = Path(original_filename).suffix
    return f"{timestamp}_{unique_id}{extension}"


def get_file_size_mb(filepath: Path) -> float:
    """Get file size in megabytes."""
    return filepath.stat().st_size / (1024 * 1024)


def get_image_resolution(filepath: Path) -> tuple:
    """
    Get image resolution (width, height).
    
    Args:
        filepath: Path to image file
        
    Returns:
        Tuple of (width, height)
    """
    image = cv2.imread(str(filepath))
    if image is None:
        raise ValueError(f"Could not read image at {filepath}")
    height, width = image.shape[:2]
    return width, height


def format_time(seconds: float) -> str:
    """
    Format time in seconds to human-readable string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string (e.g., "2.34s" or "1m 23s")
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.2f}s"


def calculate_iou(box1: list, box2: list) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.
    
    Args:
        box1: [x1, y1, x2, y2]
        box2: [x1, y1, x2, y2]
        
    Returns:
        IoU score (0-1)
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    
    # Calculate intersection area
    x_inter_min = max(x1_min, x2_min)
    y_inter_min = max(y1_min, y2_min)
    x_inter_max = min(x1_max, x2_max)
    y_inter_max = min(y1_max, y2_max)
    
    if x_inter_max < x_inter_min or y_inter_max < y_inter_min:
        return 0.0
    
    inter_area = (x_inter_max - x_inter_min) * (y_inter_max - y_inter_min)
    
    # Calculate union area
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = box1_area + box2_area - inter_area
    
    return inter_area / union_area if union_area > 0 else 0.0


def non_max_suppression(
    boxes: list,
    scores: list,
    classes: list,
    iou_threshold: float = 0.5
) -> tuple:
    """
    Apply Non-Maximum Suppression to remove overlapping detections.
    
    Args:
        boxes: List of bounding boxes [[x1,y1,x2,y2], ...]
        scores: List of confidence scores
        classes: List of class IDs
        iou_threshold: IoU threshold for suppression
        
    Returns:
        Tuple of (filtered_boxes, filtered_scores, filtered_classes)
    """
    if not boxes:
        return [], [], []
    
    # Convert to numpy arrays for easier manipulation
    boxes = np.array(boxes)
    scores = np.array(scores)
    classes = np.array(classes)
    
    # Sort by score (descending)
    indices = np.argsort(scores)[::-1]
    
    keep = []
    while len(indices) > 0:
        current = indices[0]
        keep.append(current)
        
        if len(indices) == 1:
            break
        
        # Calculate IoU with remaining boxes
        current_box = boxes[current]
        rest_boxes = boxes[indices[1:]]
        
        ious = np.array([
            calculate_iou(current_box.tolist(), box.tolist())
            for box in rest_boxes
        ])
        
        # Keep boxes with IoU below threshold
        indices = indices[1:][ious < iou_threshold]
    
    return (
        boxes[keep].tolist(),
        scores[keep].tolist(),
        classes[keep].tolist()
    )


def create_detection_dict(
    boxes: list,
    scores: list,
    classes: list,
    inference_time: float
) -> Dict[str, Any]:
    """
    Create standardized detection dictionary.
    
    Args:
        boxes: List of bounding boxes
        scores: List of confidence scores
        classes: List of class IDs
        inference_time: Time taken for inference
        
    Returns:
        Dictionary with detection data
    """
    return {
        'boxes': boxes,
        'scores': scores,
        'classes': classes,
        'count': len(boxes),
        'inference_time': inference_time
    }


def cleanup_old_files(directory: Path, max_age_seconds: int):
    """
    Remove files older than max_age_seconds from directory.
    
    Args:
        directory: Directory to clean
        max_age_seconds: Maximum file age in seconds
    """
    if not directory.exists():
        return
    
    current_time = time.time()
    
    for file_path in directory.iterdir():
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")


def ensure_dir_exists(directory: Path):
    """Create directory if it doesn't exist."""
    directory.mkdir(parents=True, exist_ok=True)