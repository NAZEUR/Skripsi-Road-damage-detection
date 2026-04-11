"""
YOLO Detector
Wrapper class for YOLOv11 model inference.
"""
import time
from pathlib import Path
from typing import Dict, Any
import numpy as np
import torch
from ultralytics import YOLO
from app.config import Config
from app.utils import create_detection_dict


class YOLODetector:
    """YOLOv11 detector with singleton pattern."""
    
    _instance = None
    
    def __new__(cls):
        """Implement singleton pattern to load model only once."""
        if cls._instance is None:
            cls._instance = super(YOLODetector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize YOLO detector (only runs once due to singleton)."""
        if self._initialized:
            return
        
        self.model_path = Config.MODEL_PATH
        self.device = Config.DEVICE
        self.model = None
        self._initialized = True
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load YOLOv11 model from weights file."""
        try:
            print(f"Loading YOLO model from {self.model_path}...")
            
            # Check if model file exists
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Model weights not found at {self.model_path}. "
                    f"Please place your trained best.pt file in the weights folder."
                )
            
            # Load model
            self.model = YOLO(str(self.model_path))
            
            # Set device
            if self.device == 'cuda' and not torch.cuda.is_available():
                print("CUDA not available. Falling back to CPU.")
                self.device = 'cpu'
            
            self.model.to(self.device)
            
            print(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLO model: {str(e)}")
    
    def predict(
        self,
        image: np.ndarray,
        conf_threshold: float = None
    ) -> Dict[str, Any]:
        """
        Run inference on image.
        
        Args:
            image: Input image as numpy array (BGR format)
            conf_threshold: Confidence threshold (uses default if None)
            
        Returns:
            Dictionary with detection results:
                - boxes: List of bounding boxes [[x1,y1,x2,y2], ...]
                - scores: List of confidence scores
                - classes: List of class IDs
                - count: Number of detections
                - inference_time: Time taken in seconds
                
        Raises:
            RuntimeError: If prediction fails
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        if conf_threshold is None:
            conf_threshold = Config.DEFAULT_CONF_THRESHOLD
        
        try:
            # Start timer
            start_time = time.time()
            
            # Run inference
            results = self.model.predict(
                image,
                conf=conf_threshold,
                device=self.device,
                verbose=False
            )[0]
            
            # End timer
            inference_time = time.time() - start_time
            
            # Parse results
            boxes = []
            scores = []
            classes = []
            
            if results.boxes is not None and len(results.boxes) > 0:
                boxes_data = results.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
                scores_data = results.boxes.conf.cpu().numpy()
                classes_data = results.boxes.cls.cpu().numpy()
                
                for box, score, cls in zip(boxes_data, scores_data, classes_data):
                    boxes.append(box.tolist())
                    scores.append(float(score))
                    classes.append(int(cls))
            
            return create_detection_dict(
                boxes=boxes,
                scores=scores,
                classes=classes,
                inference_time=inference_time
            )
            
        except Exception as e:
            raise RuntimeError(f"Prediction failed: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            Dictionary with model details
        """
        return {
            'model_path': str(self.model_path),
            'device': self.device,
            'loaded': self.model is not None,
            'classes': Config.CLASS_NAMES
        }
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None