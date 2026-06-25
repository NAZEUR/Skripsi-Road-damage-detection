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
        overlay = image.copy()
        texts_to_draw = []
        
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
                overlay,
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
                overlay,
                (x1, label_y - text_height - self.text_padding),
                (x1 + text_width + self.text_padding * 2, label_y + baseline),
                color,
                -1  # Filled rectangle
            )
            
            # Queue label text to draw later on top of blended image
            texts_to_draw.append({
                "text": label,
                "pos": (x1 + self.text_padding, label_y - baseline),
                "scale": self.font_scale,
                "color": (255, 255, 255),  # White text
                "thickness": self.font_thickness
            })
        
        # Apply transparency to boxes and backgrounds
        alpha = 0.5  # Adjust this value to make overlay more/less transparent
        cv2.addWeighted(overlay, alpha, output_image, 1 - alpha, 0, output_image)
        
        # Draw all text on the blended image so it remains fully legible
        for t in texts_to_draw:
            cv2.putText(
                output_image,
                t["text"],
                t["pos"],
                self.font,
                t["scale"],
                t["color"],
                t["thickness"],
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

    def draw_merged_detections(
        self,
        image: np.ndarray,
        ground_truths: List[Dict[str, Any]],
        predictions: Dict[str, Any]
    ) -> np.ndarray:
        """
        Draw both ground truth and predicted bounding boxes on the same image.
        Ground truth boxes are drawn with a distinct color and style to differentiate.
        """
        output_image = image.copy()
        overlay = image.copy()
        texts_to_draw = []
        
        # 1. Draw Ground Truths (Green boxes)
        gt_color = (0, 255, 0) # Green for GT
        img_h, img_w = image.shape[:2]
        
        for gt in ground_truths:
            cls_id = gt['class']
            nx, ny, nw, nh = gt['bbox']
            
            # Un-normalize
            x_center = int(nx * img_w)
            y_center = int(ny * img_h)
            box_w = int(nw * img_w)
            box_h = int(nh * img_h)
            
            x1 = int(x_center - box_w / 2)
            y1 = int(y_center - box_h / 2)
            x2 = int(x_center + box_w / 2)
            y2 = int(y_center + box_h / 2)
            
            class_name = self.class_names.get(cls_id, f"Class {cls_id}")
            
            # Draw GT box (slightly thicker, solid)
            cv2.rectangle(overlay, (x1, y1), (x2, y2), gt_color, self.box_thickness)
            
            label = f"{class_name} [GT]"
            (text_width, text_height), baseline = cv2.getTextSize(label, self.font, self.font_scale, self.font_thickness)
            label_y = max(y1 - 10, text_height + self.text_padding)
            cv2.rectangle(overlay, (x1, label_y - text_height - self.text_padding), (x1 + text_width + self.text_padding * 2, label_y + baseline), gt_color, -1)
            
            texts_to_draw.append({
                "text": label,
                "pos": (x1 + self.text_padding, label_y - baseline),
                "scale": self.font_scale,
                "color": (0, 0, 0),
                "thickness": self.font_thickness
            })

        # 2. Draw Predictions (Using class colors, slightly thinner or standard)
        boxes = predictions.get('boxes', [])
        scores = predictions.get('scores', [])
        classes = predictions.get('classes', [])
        
        for box, score, cls in zip(boxes, scores, classes):
            x1, y1, x2, y2 = map(int, box)
            # Use red if the class color is green to avoid confusion, or just use the config color
            color = self.class_colors.get(cls, (0, 0, 255)) 
            if color == (0, 255, 0): # If class color is exactly green, use red instead for prediction to contrast GT
                color = (0, 0, 255)
                
            class_name = self.class_names.get(cls, f"Class {cls}")
            
            # Draw Pred box (dashed effect could be done but standard rect is simpler, maybe thinner)
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, max(1, self.box_thickness - 1))
            
            label = f"{class_name} [Pred]: {score:.2f}"
            (text_width, text_height), baseline = cv2.getTextSize(label, self.font, self.font_scale * 0.8, self.font_thickness - 1)
            # Put label at the bottom of the box to avoid overlapping GT label at the top
            label_y = min(y2 + text_height + self.text_padding, img_h - 10)
            cv2.rectangle(overlay, (x1, label_y - text_height - self.text_padding), (x1 + text_width + self.text_padding * 2, label_y + baseline), color, -1)
            
            texts_to_draw.append({
                "text": label,
                "pos": (x1 + self.text_padding, label_y - baseline),
                "scale": self.font_scale * 0.8,
                "color": (255, 255, 255),
                "thickness": self.font_thickness - 1
            })

        # Apply transparency to both GT and Prediction boxes
        alpha = 0.5  # Transparency level
        cv2.addWeighted(overlay, alpha, output_image, 1 - alpha, 0, output_image)
        
        # Draw all text on the blended image so it remains fully legible
        for t in texts_to_draw:
            cv2.putText(output_image, t["text"], t["pos"], self.font, t["scale"], t["color"], t["thickness"], cv2.LINE_AA)

        return output_image
        
    def save_merged_visualization(
        self,
        image: np.ndarray,
        ground_truths: List[Dict[str, Any]],
        predictions: Dict[str, Any],
        output_path: Path
    ) -> str:
        """
        Draw merged detections and save result image.
        """
        try:
            output_image = self.draw_merged_detections(image, ground_truths, predictions)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            success = cv2.imwrite(str(output_path), output_image)
            if not success:
                raise RuntimeError("Failed to save merged image")
            return str(output_path)
        except Exception as e:
            raise RuntimeError(f"Merged visualization failed: {str(e)}")

    def save_heatmap_visualization(
        self,
        image: np.ndarray,
        detections: Dict[str, Any],
        output_path: Path
    ) -> str:
        """
        Draw a heatmap based on detections and save result image.
        """
        try:
            h, w = image.shape[:2]
            # Create empty heatmap
            heatmap = np.zeros((h, w), dtype=np.float32)
            
            boxes = detections.get('boxes', [])
            scores = detections.get('scores', [])
            
            for box, score in zip(boxes, scores):
                x1, y1, x2, y2 = map(int, box)
                
                # Center of the box
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                
                # Radius based on box size
                radius_x = max((x2 - x1) // 2, 10)
                radius_y = max((y2 - y1) // 2, 10)
                
                # Create a local grid
                Y, X = np.ogrid[-cy:h-cy, -cx:w-cx]
                
                # Gaussian blob
                sigma_x = radius_x / 2.0
                sigma_y = radius_y / 2.0
                
                blob = np.exp(-(X**2 / (2 * sigma_x**2) + Y**2 / (2 * sigma_y**2)))
                # Scale by confidence score
                blob = blob * score
                
                # Add to heatmap
                heatmap = np.maximum(heatmap, blob)
                
            # Normalize heatmap
            if np.max(heatmap) > 0:
                heatmap = (heatmap / np.max(heatmap) * 255).astype(np.uint8)
            else:
                heatmap = heatmap.astype(np.uint8)
                
            # Apply colormap
            heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            
            # Overlay on original image with transparency
            output_image = cv2.addWeighted(image, 0.5, heatmap_colored, 0.5, 0)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save image
            success = cv2.imwrite(str(output_path), output_image)
            
            if not success:
                raise RuntimeError("Failed to save heatmap image")
            
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Heatmap visualization failed: {str(e)}")
    
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