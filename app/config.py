"""
Application Configuration
Contains all settings, paths, and constants for the Road Damage Detection system.
"""
from pathlib import Path
from typing import Dict, Tuple


class Config:
    """Main configuration class for the application."""
    
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    OUTPUT_FOLDER = BASE_DIR / 'outputs'
    WEIGHTS_FOLDER = BASE_DIR / 'weights'
    
    # Model settings
    MODEL_PATH = WEIGHTS_FOLDER / 'best.pt'
    DEVICE = 'cuda'  # Use 'cpu' if no GPU available
    
    # File upload settings
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'zip'}
    
    # Detection parameters - defaults
    DEFAULT_CONF_THRESHOLD = 0.25
    DEFAULT_SLICE_HEIGHT = 640
    DEFAULT_SLICE_WIDTH = 640
    DEFAULT_OVERLAP_RATIO = 0.2
    DEFAULT_MATCH_THRESHOLD = 0.5
    
    # Detection parameters - ranges
    MIN_CONF_THRESHOLD = 0.1
    MAX_CONF_THRESHOLD = 0.9
    MIN_SLICE_SIZE = 320
    MAX_SLICE_SIZE = 1024
    MIN_OVERLAP_RATIO = 0.1
    MAX_OVERLAP_RATIO = 0.5
    MIN_MATCH_THRESHOLD = 0.3
    MAX_MATCH_THRESHOLD = 0.7
    
    # RDD2022 Dataset classes
    CLASS_NAMES: Dict[int, str] = {
        0: 'D00 - Longitudinal Crack',
        1: 'D10 - Transverse Crack',
        2: 'D20 - Alligator Crack',
        3: 'D40 - Pothole'
    }
    
    # Class colors (BGR format for OpenCV)
    CLASS_COLORS: Dict[int, Tuple[int, int, int]] = {
        0: (0, 0, 255),      # Red for D00
        1: (255, 0, 0),      # Blue for D10
        2: (0, 255, 0),      # Green for D20
        3: (0, 255, 255)     # Yellow for D40
    }
    
    # Class colors (RGB format for frontend)
    CLASS_COLORS_RGB: Dict[int, str] = {
        0: '#FF0000',  # Red
        1: '#0000FF',  # Blue
        2: '#00FF00',  # Green
        3: '#FFFF00'   # Yellow
    }
    
    # Flask settings
    SECRET_KEY = 'your-secret-key-change-in-production'
    DEBUG = True
    
    # File cleanup settings (in seconds)
    FILE_RETENTION_TIME = 3600  # 1 hour
    
    @classmethod
    def ensure_folders_exist(cls):
        """Create necessary folders if they don't exist."""
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.WEIGHTS_FOLDER.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings."""
        if not cls.MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model weights not found at {cls.MODEL_PATH}. "
                f"Please place your trained best.pt file in the weights folder."
            )
        return True