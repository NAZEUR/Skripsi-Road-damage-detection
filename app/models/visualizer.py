"""
Detection Visualizer
Draws bounding boxes, labels, and confidence scores on images.
"""
import cv2
import numpy as np
from typing import Dict, Any, List
from pathlib import Path
from app.config import Config


class DetectionVisualizer:
    """Visualizes detection results on images."""
    
    def __init__(self):
        """Initialize visualizer with default settings."""
        self.class_names = Config.CLASS_NAMES
        self.class_colors = Config.CLASS_COLORS
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2
        self.box_thickness = 3
        self.text_padding = 5
    
    def draw_detections(
        self,
        image: np.ndarray,
        detections: Dict[str, Any]
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels on image.
        
        Args:
            image: Input image as numpy array (BGR format)
            detections: Detection results dictionary with boxes, scores, classes
            
        Returns:
            Image with drawn detections
        """
        # Create a copy to avoid modifying original
        output_image = image.copy()
        
        boxes = detections.get('boxes', [])
        scores = detections.get('scores', [])
        classes = detections.get('classes', [])
        
        for box, score, cls in zip(boxes, scores, classes):
            # Convert box coordinates to integers
            x1, y1, x2, y2 = map(int, box)
            
            # Get class color and name
            color = self.class_colors.get(cls, (255, 255, 255))
            class_name = self.class_names.get(cls, f"Class {cls}")
            
            # Draw bounding box
            cv2.rectangle(
                output_image,
                (x1, y1),
                (x2, y2),
                color,
                self.box_thickness
            )
            
            # Prepare label text
            label = f"{class_name}: {score:.2f}"
            
            # Calculate text size for background
            (text_width, text_height), baseline = cv2.getTextSize(
                label,
                self.font,
                self.font_scale,
                self.font_thickness
            )
            
            # Draw label background
            label_y = max(y1 - 10, text_height + self.text_padding)
            cv2.rectangle(
                output_image,
                (x1, label_y - text_height - self.text_padding),
                (x1 + text_width + self.text_padding * 2, label_y + baseline),
                color,
                -1  # Filled rectangle
            )
            
            # Draw label text
            cv2.putText(
                output_image,
                label,
                (x1 + self.text_padding, label_y - baseline),
                self.font,
                self.font_scale,
                (255, 255, 255),  # White text
                self.font_thickness,
                cv2.LINE_AA
            )
        
        return output_image
    
    def save_visualization(
        self,
        image: np.ndarray,
        detections: Dict[str, Any],
        output_path: Path
    ) -> str:
        """
        Draw detections and save result image.
        
        Args:
            image: Input image as numpy array (BGR format)
            detections: Detection results dictionary
            output_path: Path to save output image
            
        Returns:
            Path to saved image
            
        Raises:
            RuntimeError: If saving fails
        """
        try:
            # Draw detections
            output_image = self.draw_detections(image, detections)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save image
            success = cv2.imwrite(str(output_path), output_image)
            
            if not success:
                raise RuntimeError("Failed to save image")
            
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Visualization failed: {str(e)}")
    
    def create_side_by_side(
        self,
        original_image: np.ndarray,
        result_image: np.ndarray,
        output_path: Path
    ) -> str:
        """
        Create side-by-side comparison image.
        
        Args:
            original_image: Original input image
            result_image: Image with detections drawn
            output_path: Path to save comparison image
            
        Returns:
            Path to saved comparison image
            
        Raises:
            RuntimeError: If creation fails
        """
        try:
            # Resize images to same height if needed
            h1, w1 = original_image.shape[:2]
            h2, w2 = result_image.shape[:2]
            
            if h1 != h2:
                # Resize to match heights
                target_height = min(h1, h2)
                original_image = cv2.resize(
                    original_image,
                    (int(w1 * target_height / h1), target_height)
                )
                result_image = cv2.resize(
                    result_image,
                    (int(w2 * target_height / h2), target_height)
                )
            
            # Add labels
            original_labeled = self._add_title(original_image, "Original")
            result_labeled = self._add_title(result_image, "Detection Result")
            
            # Concatenate horizontally
            comparison = np.hstack([original_labeled, result_labeled])
            
            # Save comparison image
            output_path.parent.mkdir(parents=True, exist_ok=True)
            success = cv2.imwrite(str(output_path), comparison)
            
            if not success:
                raise RuntimeError("Failed to save comparison image")
            
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Side-by-side creation failed: {str(e)}")
    
    def _add_title(self, image: np.ndarray, title: str) -> np.ndarray:
        """Add title text to top of image."""
        # Create copy
        img_with_title = image.copy()
        
        # Calculate title position
        (text_width, text_height), baseline = cv2.getTextSize(
            title,
            self.font,
            self.font_scale * 1.5,
            self.font_thickness
        )
        
        # Add white background for title
        title_height = text_height + baseline + self.text_padding * 2
        title_bg = np.ones((title_height, img_with_title.shape[1], 3), dtype=np.uint8) * 255
        
        # Draw title text
        text_x = (img_with_title.shape[1] - text_width) // 2
        cv2.putText(
            title_bg,
            title,
            (text_x, text_height + self.text_padding),
            self.font,
            self.font_scale * 1.5,
            (0, 0, 0),  # Black text
            self.font_thickness,
            cv2.LINE_AA
        )
        
        # Concatenate title with image
        return np.vstack([title_bg, img_with_title])