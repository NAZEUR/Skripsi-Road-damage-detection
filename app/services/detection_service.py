"""
Detection Service
Main orchestrator for road damage detection operations.
Coordinates between detector, SAHI processor, visualizer, and file handler.
"""
import json
import time
from pathlib import Path
from typing import Dict, Any
from app.config import Config
from app.models import YOLODetector, SAHIProcessor, DetectionVisualizer
from app.services.file_handler import FileHandler
from app.services.image_processor import ImageProcessor
from app.utils import format_time


class DetectionService:
    """Main service for detection operations with singleton pattern."""
    
    _instance = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(DetectionService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize detection service (only runs once due to singleton)."""
        if self._initialized:
            return
        
        # Initialize components
        self.detector = YOLODetector()
        self.sahi_processor = SAHIProcessor()
        self.visualizer = DetectionVisualizer()
        self.file_handler = FileHandler()
        self.image_processor = ImageProcessor()
        self._initialized = True
    
    def detect_baseline(
        self,
        image_path: str,
        conf_threshold: float = None
    ) -> Dict[str, Any]:
        """
        Perform baseline detection using direct YOLO inference.
        
        Args:
            image_path: Path to input image
            conf_threshold: Confidence threshold for detections
            
        Returns:
            Dictionary with detection results
            
        Raises:
            RuntimeError: If detection fails
        """
        if conf_threshold is None:
            conf_threshold = Config.DEFAULT_CONF_THRESHOLD
        
        try:
            # Load image
            image = self.file_handler.load_image(image_path)
            
            # Run detection
            detections = self.detector.predict(
                image=image,
                conf_threshold=conf_threshold
            )
            
            return detections
            
        except Exception as e:
            raise RuntimeError(f"Baseline detection failed: {str(e)}")
    
    def detect_sahi(
        self,
        image_path: str,
        slice_height: int = None,
        slice_width: int = None,
        overlap_ratio: float = None,
        match_threshold: float = None,
        conf_threshold: float = None
    ) -> Dict[str, Any]:
        """
        Perform SAHI detection using sliced inference.
        
        Args:
            image_path: Path to input image
            slice_height: Height of each slice
            slice_width: Width of each slice
            overlap_ratio: Overlap ratio between slices
            match_threshold: IoU threshold for merging detections
            conf_threshold: Confidence threshold for detections
            
        Returns:
            Dictionary with detection results including num_slices
            
        Raises:
            RuntimeError: If detection fails
        """
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
            # Load image
            image = self.file_handler.load_image(image_path)
            
            # Run SAHI detection
            detections = self.sahi_processor.process(
                image=image,
                slice_height=slice_height,
                slice_width=slice_width,
                overlap_ratio=overlap_ratio,
                match_threshold=match_threshold,
                conf_threshold=conf_threshold
            )
            
            return detections
            
        except Exception as e:
            raise RuntimeError(f"SAHI detection failed: {str(e)}")
    
    def visualize_results(
        self,
        image_path: str,
        detections: Dict[str, Any],
        output_filename: str
    ) -> str:
        """
        Visualize detection results and save output image.
        
        Args:
            image_path: Path to input image
            detections: Detection results dictionary
            output_filename: Filename for output image
            
        Returns:
            Path to output image
            
        Raises:
            RuntimeError: If visualization fails
        """
        try:
            # Load image
            image = self.file_handler.load_image(image_path)
            
            # Generate output path
            output_path = self.file_handler.get_output_path(
                output_filename,
                suffix="_result"
            )
            
            # Save visualization
            result_path = self.visualizer.save_visualization(
                image=image,
                detections=detections,
                output_path=output_path
            )
            
            return result_path
            
        except Exception as e:
            raise RuntimeError(f"Visualization failed: {str(e)}")
    
    def calculate_statistics(
        self,
        detections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate statistics from detection results.
        
        Args:
            detections: Detection results dictionary
            
        Returns:
            Dictionary with statistics:
                - total_detections: Total number of detections
                - detections_by_class: Count per class
                - average_confidence: Average confidence score
                - inference_time: Time taken for inference
                - inference_time_formatted: Human-readable time
        """
        boxes = detections.get('boxes', [])
        scores = detections.get('scores', [])
        classes = detections.get('classes', [])
        inference_time = detections.get('inference_time', 0)
        
        # Count detections by class
        detections_by_class = {}
        for cls in classes:
            class_name = Config.CLASS_NAMES.get(cls, f"Class {cls}")
            detections_by_class[class_name] = detections_by_class.get(class_name, 0) + 1
        
        # Calculate average confidence
        avg_confidence = sum(scores) / len(scores) if scores else 0.0
        
        statistics = {
            'total_detections': len(boxes),
            'detections_by_class': detections_by_class,
            'average_confidence': round(avg_confidence, 3),
            'inference_time': round(inference_time, 3),
            'inference_time_formatted': format_time(inference_time)
        }
        
        # Add SAHI-specific stats if available
        if 'num_slices' in detections:
            statistics['num_slices'] = detections['num_slices']
        
        return statistics
    
    def export_json(
        self,
        detections: Dict[str, Any],
        statistics: Dict[str, Any],
        image_info: Dict[str, Any],
        output_filename: str
    ) -> str:
        """
        Export detection results to JSON file.
        
        Args:
            detections: Detection results dictionary
            statistics: Statistics dictionary
            image_info: Image information
            output_filename: Filename for output JSON
            
        Returns:
            Path to JSON file
            
        Raises:
            RuntimeError: If export fails
        """
        try:
            # Prepare export data
            export_data = {
                'image_info': image_info,
                'statistics': statistics,
                'detections': {
                    'boxes': detections.get('boxes', []),
                    'scores': detections.get('scores', []),
                    'classes': detections.get('classes', []),
                    'class_names': [
                        Config.CLASS_NAMES.get(cls, f"Class {cls}")
                        for cls in detections.get('classes', [])
                    ]
                }
            }
            
            # Generate output path
            output_path = self.file_handler.get_output_path(
                output_filename,
                suffix="_data.json"
            )
            
            # Write JSON file
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"JSON export failed: {str(e)}")
    
    def process_detection(
        self,
        image_path: str,
        mode: str = 'baseline',
        **params
    ) -> Dict[str, Any]:
        """
        Complete detection workflow: detect, visualize, calculate stats, export.
        
        Args:
            image_path: Path to input image
            mode: Detection mode ('baseline' or 'sahi')
            **params: Additional parameters for detection
            
        Returns:
            Dictionary with complete results:
                - detections: Detection results
                - statistics: Statistics
                - output: Paths to output files
                
        Raises:
            ValueError: If mode is invalid
            RuntimeError: If processing fails
        """
        try:
            # Validate mode
            if mode not in ['baseline', 'sahi']:
                raise ValueError(f"Invalid mode: {mode}. Must be 'baseline' or 'sahi'")
            
            # Run detection
            if mode == 'baseline':
                detections = self.detect_baseline(
                    image_path=image_path,
                    conf_threshold=params.get('confidence')
                )
            else:  # sahi
                detections = self.detect_sahi(
                    image_path=image_path,
                    slice_height=params.get('slice_height'),
                    slice_width=params.get('slice_width'),
                    overlap_ratio=params.get('overlap_ratio'),
                    match_threshold=params.get('match_threshold'),
                    conf_threshold=params.get('confidence')
                )
            
            # Get image info
            image = self.file_handler.load_image(image_path)
            image_info = self.image_processor.get_image_info(image)
            
            # Calculate statistics
            statistics = self.calculate_statistics(detections)
            
            # Generate output filename
            original_filename = Path(image_path).name
            
            # Visualize results
            output_image_path = self.visualize_results(
                image_path=image_path,
                detections=detections,
                output_filename=original_filename
            )
            
            # Export JSON
            output_json_path = self.export_json(
                detections=detections,
                statistics=statistics,
                image_info=image_info,
                output_filename=original_filename
            )
            
            return {
                'detections': detections,
                'statistics': statistics,
                'output': {
                    'image': output_image_path,
                    'json': output_json_path
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"Detection processing failed: {str(e)}")
    
    def check_model_status(self) -> Dict[str, Any]:
        """
        Check if models are loaded and ready.
        
        Returns:
            Dictionary with model status information
        """
        return {
            'detector_loaded': self.detector.is_loaded(),
            'sahi_loaded': self.sahi_processor.is_loaded(),
            'model_info': self.detector.get_model_info(),
            'device_active': self.detector.device if hasattr(self.detector, 'device') else Config.DEVICE,
            'ready': self.detector.is_loaded() and self.sahi_processor.is_loaded()
        }

    def switch_device(self, device: str) -> Dict[str, Any]:
        """Switch the inference device (cpu/cuda) for both models."""
        try:
            self.detector.switch_device(device)
            self.sahi_processor.switch_device(device)
            return {
                'success': True,
                'status': self.check_model_status()
            }
        except Exception as e:
            raise RuntimeError(f"Failed to switch device: {str(e)}")