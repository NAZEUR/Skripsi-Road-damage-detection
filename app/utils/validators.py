"""
Input Validation Utilities
Validates file uploads, detection parameters, and other user inputs.
"""
from pathlib import Path
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage
from app.config import Config


class FileValidator:
    """Validates uploaded files."""
    
    @staticmethod
    def validate_file(file: FileStorage) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file.
        
        Args:
            file: Uploaded file from Flask request
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"
        
        if file.filename == '':
            return False, "No file selected"
        
        # Check file extension
        if not FileValidator.allowed_file(file.filename):
            allowed = ', '.join(Config.ALLOWED_EXTENSIONS)
            return False, f"Invalid file type. Allowed: {allowed}"
        
        # Check file size (if possible)
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if size > Config.MAX_CONTENT_LENGTH:
            max_mb = Config.MAX_CONTENT_LENGTH / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_mb}MB"
        
        return True, None
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


class ParameterValidator:
    """Validates detection parameters."""
    
    @staticmethod
    def validate_confidence(conf: float) -> Tuple[bool, Optional[str]]:
        """Validate confidence threshold."""
        if not Config.MIN_CONF_THRESHOLD <= conf <= Config.MAX_CONF_THRESHOLD:
            return False, (
                f"Confidence must be between "
                f"{Config.MIN_CONF_THRESHOLD} and {Config.MAX_CONF_THRESHOLD}"
            )
        return True, None
    
    @staticmethod
    def validate_slice_size(size: int) -> Tuple[bool, Optional[str]]:
        """Validate slice height/width."""
        if not Config.MIN_SLICE_SIZE <= size <= Config.MAX_SLICE_SIZE:
            return False, (
                f"Slice size must be between "
                f"{Config.MIN_SLICE_SIZE} and {Config.MAX_SLICE_SIZE}"
            )
        return True, None
    
    @staticmethod
    def validate_overlap_ratio(ratio: float) -> Tuple[bool, Optional[str]]:
        """Validate overlap ratio."""
        if not Config.MIN_OVERLAP_RATIO <= ratio <= Config.MAX_OVERLAP_RATIO:
            return False, (
                f"Overlap ratio must be between "
                f"{Config.MIN_OVERLAP_RATIO} and {Config.MAX_OVERLAP_RATIO}"
            )
        return True, None
    
    @staticmethod
    def validate_match_threshold(threshold: float) -> Tuple[bool, Optional[str]]:
        """Validate match threshold."""
        if not Config.MIN_MATCH_THRESHOLD <= threshold <= Config.MAX_MATCH_THRESHOLD:
            return False, (
                f"Match threshold must be between "
                f"{Config.MIN_MATCH_THRESHOLD} and {Config.MAX_MATCH_THRESHOLD}"
            )
        return True, None
    
    @staticmethod
    def validate_detection_params(params: dict) -> Tuple[bool, Optional[str]]:
        """
        Validate all detection parameters.
        
        Args:
            params: Dictionary of detection parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate confidence
        if 'confidence' in params:
            valid, error = ParameterValidator.validate_confidence(
                params['confidence']
            )
            if not valid:
                return False, error
        
        # Validate slice sizes (for SAHI mode)
        if params.get('mode') == 'sahi':
            if 'slice_height' in params:
                valid, error = ParameterValidator.validate_slice_size(
                    params['slice_height']
                )
                if not valid:
                    return False, error
            
            if 'slice_width' in params:
                valid, error = ParameterValidator.validate_slice_size(
                    params['slice_width']
                )
                if not valid:
                    return False, error
            
            if 'overlap_ratio' in params:
                valid, error = ParameterValidator.validate_overlap_ratio(
                    params['overlap_ratio']
                )
                if not valid:
                    return False, error
            
            if 'match_threshold' in params:
                valid, error = ParameterValidator.validate_match_threshold(
                    params['match_threshold']
                )
                if not valid:
                    return False, error
        
        return True, None


class PathValidator:
    """Validates file paths for security."""
    
    @staticmethod
    def validate_path(filepath: str, base_dir: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate that filepath is within base directory (prevent path traversal).
        
        Args:
            filepath: Path to validate
            base_dir: Base directory that should contain the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            file_path = Path(filepath).resolve()
            base_path = base_dir.resolve()
            
            # Check if file is within base directory
            if not str(file_path).startswith(str(base_path)):
                return False, "Invalid file path"
            
            return True, None
        except Exception as e:
            return False, f"Path validation error: {str(e)}"