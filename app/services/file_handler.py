"""
File Handler Service
Handles file upload, validation, storage, and cleanup operations.
"""
import cv2
from pathlib import Path
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from app.config import Config
from app.utils import (
    FileValidator,
    PathValidator,
    generate_unique_filename,
    get_file_size_mb,
    get_image_resolution,
    cleanup_old_files,
    ensure_dir_exists
)


class FileHandler:
    """Handles file operations with singleton pattern."""
    
    _instance = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(FileHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize file handler (only runs once due to singleton)."""
        if self._initialized:
            return
        
        self.upload_folder = Config.UPLOAD_FOLDER
        self.output_folder = Config.OUTPUT_FOLDER
        self._initialized = True
        
        # Ensure folders exist
        ensure_dir_exists(self.upload_folder)
        ensure_dir_exists(self.output_folder)
    
    def save_uploaded_file(self, file: FileStorage) -> Dict[str, Any]:
        """
        Validate and save uploaded file.
        
        Args:
            file: Uploaded file from Flask request
            
        Returns:
            Dictionary with file information:
                - filepath: Path to saved file
                - filename: Original filename
                - size: File size in MB
                - resolution: Image resolution (width x height)
                
        Raises:
            ValueError: If file validation fails
            RuntimeError: If file saving fails
        """
        # Validate file
        is_valid, error_message = FileValidator.validate_file(file)
        if not is_valid:
            raise ValueError(error_message)
        
        try:
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            unique_filename = generate_unique_filename(original_filename)
            
            # Save file
            filepath = self.upload_folder / unique_filename
            file.save(str(filepath))
            
            file_size = get_file_size_mb(filepath)
            
            if original_filename.lower().endswith('.zip'):
                import zipfile
                extracted_dir = self.upload_folder / f"{unique_filename}_extracted"
                ensure_dir_exists(extracted_dir)
                
                image_files = []
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(extracted_dir)
                    for extracted_file in extracted_dir.rglob('*'):
                        if extracted_file.is_file():
                            ext = extracted_file.name.lower().split('.')[-1]
                            if ext in ['jpg', 'jpeg', 'png', 'bmp']:
                                image_files.append({
                                    'filepath': str(extracted_file),
                                    'filename': extracted_file.name
                                })
                
                return {
                    'filepath': str(filepath),
                    'filename': original_filename,
                    'is_zip': True,
                    'extracted_files': image_files,
                    'size': round(file_size, 2)
                }
            
            # Normal single image processing
            width, height = get_image_resolution(filepath)
            
            return {
                'filepath': str(filepath),
                'filename': original_filename,
                'size': round(file_size, 2),
                'resolution': f"{width}x{height}",
                'is_zip': False
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to save file: {str(e)}")
    
    def load_image(self, filepath: str) -> Optional[Any]:
        """
        Load image from filepath.
        
        Args:
            filepath: Path to image file
            
        Returns:
            Image as numpy array (BGR format) or None if failed
            
        Raises:
            ValueError: If filepath is invalid
            RuntimeError: If image loading fails
        """
        # Validate path
        is_valid, error = PathValidator.validate_path(
            filepath, self.upload_folder
        )
        if not is_valid:
            # Also check output folder
            is_valid, error = PathValidator.validate_path(
                filepath, self.output_folder
            )
            if not is_valid:
                # Also check testdata folder
                testdata_dir = Config.BASE_DIR.parent / 'testdata' / 'images'
                is_valid, error = PathValidator.validate_path(
                    filepath, testdata_dir
                )
                if not is_valid:
                    raise ValueError(error)
        
        try:
            image = cv2.imread(filepath)
            if image is None:
                raise RuntimeError(f"Could not read image at {filepath}")
            return image
            
        except Exception as e:
            raise RuntimeError(f"Failed to load image: {str(e)}")
    
    def save_image(self, image: Any, filename: str) -> str:
        """
        Save image to output folder.
        
        Args:
            image: Image as numpy array (BGR format)
            filename: Filename for saved image
            
        Returns:
            Path to saved image
            
        Raises:
            RuntimeError: If saving fails
        """
        try:
            output_path = self.output_folder / filename
            success = cv2.imwrite(str(output_path), image)
            
            if not success:
                raise RuntimeError("Failed to write image")
            
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Failed to save image: {str(e)}")
    
    def cleanup_old_files(self):
        """Remove old files from upload and output folders."""
        try:
            cleanup_old_files(
                self.upload_folder,
                Config.FILE_RETENTION_TIME
            )
            cleanup_old_files(
                self.output_folder,
                Config.FILE_RETENTION_TIME
            )
        except Exception as e:
            print(f"Cleanup error: {str(e)}")
    
    def delete_file(self, filepath: str) -> bool:
        """
        Delete a specific file.
        
        Args:
            filepath: Path to file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(filepath)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {filepath}: {e}")
            return False
    
    def get_output_path(self, original_filename: str, suffix: str = "") -> Path:
        """
        Generate output file path.
        
        Args:
            original_filename: Original input filename
            suffix: Suffix to add before extension (e.g., "_result")
            
        Returns:
            Path object for output file
        """
        stem = Path(original_filename).stem
        ext = Path(original_filename).suffix
        output_filename = f"{stem}{suffix}{ext}"
        return self.output_folder / output_filename