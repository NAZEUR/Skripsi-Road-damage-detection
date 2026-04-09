"""
Image Processor Service
Handles image preprocessing operations like resizing and normalization.
"""
import cv2
import numpy as np
from typing import Tuple, Optional


class ImageProcessor:
    """Handles image preprocessing operations."""
    
    def __init__(self):
        """Initialize image processor."""
        pass
    
    def resize_image(
        self,
        image: np.ndarray,
        target_size: Optional[Tuple[int, int]] = None,
        max_size: Optional[int] = None
    ) -> np.ndarray:
        """
        Resize image to target size or maximum dimension.
        
        Args:
            image: Input image as numpy array
            target_size: Target size as (width, height) - exact resize
            max_size: Maximum dimension - maintains aspect ratio
            
        Returns:
            Resized image
        """
        if target_size is not None:
            return cv2.resize(image, target_size)
        
        if max_size is not None:
            height, width = image.shape[:2]
            
            if max(height, width) > max_size:
                if height > width:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                else:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                
                return cv2.resize(image, (new_width, new_height))
        
        return image
    
    def normalize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize image pixel values to [0, 1] range.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Normalized image
        """
        return image.astype(np.float32) / 255.0
    
    def denormalize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Denormalize image from [0, 1] to [0, 255] range.
        
        Args:
            image: Normalized image
            
        Returns:
            Denormalized image
        """
        return (image * 255).astype(np.uint8)
    
    def pad_image(
        self,
        image: np.ndarray,
        target_size: Tuple[int, int],
        padding_value: Tuple[int, int, int] = (114, 114, 114)
    ) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Pad image to target size while maintaining aspect ratio.
        
        Args:
            image: Input image
            target_size: Target size as (width, height)
            padding_value: RGB values for padding
            
        Returns:
            Tuple of (padded_image, (pad_x, pad_y))
        """
        height, width = image.shape[:2]
        target_width, target_height = target_size
        
        # Calculate scaling factor
        scale = min(target_width / width, target_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Resize image
        resized = cv2.resize(image, (new_width, new_height))
        
        # Calculate padding
        pad_x = (target_width - new_width) // 2
        pad_y = (target_height - new_height) // 2
        
        # Create padded image
        padded = np.full(
            (target_height, target_width, 3),
            padding_value,
            dtype=np.uint8
        )
        padded[pad_y:pad_y + new_height, pad_x:pad_x + new_width] = resized
        
        return padded, (pad_x, pad_y)
    
    def adjust_brightness(
        self,
        image: np.ndarray,
        factor: float = 1.0
    ) -> np.ndarray:
        """
        Adjust image brightness.
        
        Args:
            image: Input image
            factor: Brightness factor (1.0 = no change, >1.0 = brighter)
            
        Returns:
            Adjusted image
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv = hsv.astype(np.float32)
        hsv[:, :, 2] = hsv[:, :, 2] * factor
        hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)
        hsv = hsv.astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    def enhance_contrast(
        self,
        image: np.ndarray,
        clip_limit: float = 2.0
    ) -> np.ndarray:
        """
        Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        Args:
            image: Input image
            clip_limit: Threshold for contrast limiting
            
        Returns:
            Enhanced image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        
        # Convert back to BGR
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    def get_image_info(self, image: np.ndarray) -> dict:
        """
        Get information about image.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with image information
        """
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1
        
        return {
            'width': width,
            'height': height,
            'channels': channels,
            'dtype': str(image.dtype),
            'shape': image.shape
        }