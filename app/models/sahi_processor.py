"""
SAHI Processor
Sliced Aided Hyper Inference (SAHI) for detecting small objects.
"""
import time
from typing import Dict, Any
import numpy as np
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction
from app.config import Config
from app.utils import create_detection_dict, non_max_suppression


class SAHIProcessor:
    """SAHI processor for sliced inference with singleton pattern."""
    
    _instance = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(SAHIProcessor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize SAHI processor (only runs once due to singleton)."""
        if self._initialized:
            return
        
        self.model_path = Config.MODEL_PATH
        self.device = Config.DEVICE
        self.detection_model = None
        self._initialized = True
        
        # Load model for SAHI
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model for SAHI."""
        try:
            print(f"Loading SAHI detection model from {self.model_path}...")
            
            # Check if model file exists
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Model weights not found at {self.model_path}"
                )
            
            # Initialize SAHI detection model
            self.detection_model = AutoDetectionModel.from_pretrained(
                model_type='yolov8',  # YOLOv11 uses same architecture as v8
                model_path=str(self.model_path),
                confidence_threshold=Config.DEFAULT_CONF_THRESHOLD,
                device=self.device
            )
            
            print("SAHI model loaded successfully")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load SAHI model: {str(e)}")
    
    def process(
        self,
        image: np.ndarray,
        slice_height: int = None,
        slice_width: int = None,
        overlap_ratio: float = None,
        match_threshold: float = None,
        conf_threshold: float = None
    ) -> Dict[str, Any]:
        """
        Process image using SAHI sliced inference.
        
        Args:
            image: Input image as numpy array (BGR format)
            slice_height: Height of each slice in pixels
            slice_width: Width of each slice in pixels
            overlap_ratio: Overlap ratio between slices (0-1)
            match_threshold: IoU threshold for merging detections
            conf_threshold: Confidence threshold for detections
            
        Returns:
            Dictionary with detection results:
                - boxes: List of bounding boxes [[x1,y1,x2,y2], ...]
                - scores: List of confidence scores
                - classes: List of class IDs
                - count: Number of detections
                - inference_time: Time taken in seconds
                - num_slices: Number of slices processed
                
        Raises:
            RuntimeError: If processing fails
        """
        if self.detection_model is None:
            raise RuntimeError("SAHI model not loaded")
        
        # Use defaults if not provided
        if slice_height is None:
            slice_height = Config.DEFAULT_SLICE_HEIGHT
        if slice_width is None:
            slice_width = Config.DEFAULT_SLICE_WIDTH
        if overlap_ratio is None:
            overlap_ratio = Config.DEFAULT_OVERLAP_RATIO
        if match_threshold is None:
            match_threshold = Config.DEFAULT_MATCH_THRESHOLD
        if conf_threshold is None:
            conf_threshold = Config.DEFAULT_CONF_THRESHOLD
        
        try:
            # Update confidence threshold
            self.detection_model.confidence_threshold = conf_threshold
            
            # Start timer
            start_time = time.time()
            
            # Run sliced prediction
            result = get_sliced_prediction(
                image,
                self.detection_model,
                slice_height=slice_height,
                slice_width=slice_width,
                overlap_height_ratio=overlap_ratio,
                overlap_width_ratio=overlap_ratio,
                postprocess_type="NMS",
                postprocess_match_threshold=match_threshold,
                postprocess_class_agnostic=False,
                verbose=0
            )
            
            # End timer
            inference_time = time.time() - start_time
            
            # Parse results
            boxes = []
            scores = []
            classes = []
            
            for obj in result.object_prediction_list:
                bbox = obj.bbox.to_xyxy()  # [x1, y1, x2, y2]
                boxes.append(bbox)
                scores.append(float(obj.score.value))
                classes.append(int(obj.category.id))
            
            # Apply additional NMS to ensure no duplicate detections
            if boxes:
                boxes, scores, classes = non_max_suppression(
                    boxes, scores, classes, iou_threshold=match_threshold
                )
            
            # Calculate number of slices
            image_height, image_width = image.shape[:2]
            num_slices_h = int(np.ceil(image_height / (slice_height * (1 - overlap_ratio))))
            num_slices_w = int(np.ceil(image_width / (slice_width * (1 - overlap_ratio))))
            num_slices = num_slices_h * num_slices_w
            
            detection_dict = create_detection_dict(
                boxes=boxes,
                scores=scores,
                classes=classes,
                inference_time=inference_time
            )
            
            # Add SAHI-specific information
            detection_dict['num_slices'] = num_slices
            
            return detection_dict
            
        except Exception as e:
            raise RuntimeError(f"SAHI processing failed: {str(e)}")
    
    def is_loaded(self) -> bool:
        """Check if SAHI model is loaded."""
        return self.detection_model is not None