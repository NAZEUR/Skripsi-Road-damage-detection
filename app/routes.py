"""
Flask Routes
API endpoints for the road damage detection application.
"""
from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import os
from app.config import Config
from app.services import DetectionService, FileHandler
from app.utils import ParameterValidator

# Create blueprint
main_bp = Blueprint('main', __name__)

# Initialize services
detection_service = DetectionService()
file_handler = FileHandler()


@main_bp.route('/health', methods=['GET'])
def health_check():
    """
    Check if the application and models are ready.
    
    Returns:
        JSON response with health status
    """
    try:
        status = detection_service.check_model_status()
        
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy' if status['ready'] else 'not_ready',
                'models': status
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Health check failed: {str(e)}"
        }), 500


@main_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle file upload endpoint.
    
    Expected:
        multipart/form-data with 'file' field
        
    Returns:
        JSON response with file information
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided in request'
            }), 400
        
        file = request.files['file']
        
        # Save file and get info
        file_info = file_handler.save_uploaded_file(file)
        
        return jsonify({
            'success': True,
            'data': file_info
        }), 200
        
    except ValueError as e:
        # Validation error
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        # Server error
        return jsonify({
            'success': False,
            'error': f"Upload failed: {str(e)}"
        }), 500


@main_bp.route('/detect', methods=['POST'])
def detect():
    """
    Perform road damage detection.
    
    Expected JSON:
        {
            "filepath": "path/to/image.jpg",
            "mode": "baseline" | "sahi",
            "confidence": 0.25,
            // For SAHI mode:
            "slice_height": 640,
            "slice_width": 640,
            "overlap_ratio": 0.2,
            "match_threshold": 0.5
        }
        
    Returns:
        JSON response with detection results
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        if 'filepath' not in data:
            return jsonify({
                'success': False,
                'error': 'filepath is required'
            }), 400
        
        if 'mode' not in data:
            return jsonify({
                'success': False,
                'error': 'mode is required (baseline or sahi)'
            }), 400
        
        # Extract parameters
        filepath = data['filepath']
        mode = data['mode']
        confidence = data.get('confidence', Config.DEFAULT_CONF_THRESHOLD)
        
        # Prepare detection parameters
        detect_params = {
            'confidence': confidence
        }
        
        # Add SAHI-specific parameters if in SAHI mode
        if mode == 'sahi':
            detect_params.update({
                'slice_height': data.get('slice_height', Config.DEFAULT_SLICE_HEIGHT),
                'slice_width': data.get('slice_width', Config.DEFAULT_SLICE_WIDTH),
                'overlap_ratio': data.get('overlap_ratio', Config.DEFAULT_OVERLAP_RATIO),
                'match_threshold': data.get('match_threshold', Config.DEFAULT_MATCH_THRESHOLD)
            })
        
        # Validate parameters
        is_valid, error = ParameterValidator.validate_detection_params({
            'mode': mode,
            **detect_params
        })
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        # Perform detection
        result = detection_service.process_detection(
            image_path=filepath,
            mode=mode,
            **detect_params
        )
        
        # Convert absolute paths to relative URLs for frontend
        output_image_path = result['output']['image']
        output_json_path = result['output']['json']
        
        # Extract just the filename from the path
        image_filename = Path(output_image_path).name
        json_filename = Path(output_json_path).name
        
        # Create URLs that the frontend can access
        image_url = f"/view/{image_filename}"
        json_url = f"/download/{json_filename}"
        
        # Prepare response
        response_data = {
            'mode': mode,
            'detections': {
                'count': result['detections']['count'],
                'boxes': result['detections']['boxes'],
                'scores': result['detections']['scores'],
                'classes': result['detections']['classes'],
                'class_names': [
                    Config.CLASS_NAMES.get(cls, f"Class {cls}")
                    for cls in result['detections']['classes']
                ]
            },
            'statistics': result['statistics'],
            'output': {
                'image': image_url,
                'json': json_url
            }
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except ValueError as e:
        # Validation error
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        # Server error
        return jsonify({
            'success': False,
            'error': f"Detection failed: {str(e)}"
        }), 500


@main_bp.route('/view/<filename>', methods=['GET'])
def view_output_image(filename):
    """
    View output image from results.
    
    Args:
        filename: Name of the output file
        
    Returns:
        Image file or error
    """
    try:
        # Construct file path
        file_path = Config.OUTPUT_FOLDER / filename
        
        # Security check: ensure file is in output folder
        if not str(file_path).startswith(str(Config.OUTPUT_FOLDER)):
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 403
        
        # Check if file exists
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        # Send file
        return send_file(
            str(file_path),
            mimetype='image/png'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"View failed: {str(e)}"
        }), 500


@main_bp.route('/download/<path:filepath>', methods=['GET'])
def download_file(filepath):
    """
    Download a file from output directory.
    
    Args:
        filepath: Relative path to file
        
    Returns:
        File download
    """
    try:
        # Construct full path from output folder
        file_path = Config.OUTPUT_FOLDER / filepath
        
        # Security check: ensure file is in output folder
        if not str(file_path).startswith(str(Config.OUTPUT_FOLDER)):
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 403
        
        # Check if file exists
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        # Send file
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=file_path.name
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Download failed: {str(e)}"
        }), 500


@main_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get application configuration for frontend.
    
    Returns:
        JSON response with configuration
    """
    try:
        config_data = {
            'classes': Config.CLASS_NAMES,
            'colors': Config.CLASS_COLORS_RGB,
            'defaults': {
                'confidence': Config.DEFAULT_CONF_THRESHOLD,
                'slice_height': Config.DEFAULT_SLICE_HEIGHT,
                'slice_width': Config.DEFAULT_SLICE_WIDTH,
                'overlap_ratio': Config.DEFAULT_OVERLAP_RATIO,
                'match_threshold': Config.DEFAULT_MATCH_THRESHOLD
            },
            'limits': {
                'confidence': {
                    'min': Config.MIN_CONF_THRESHOLD,
                    'max': Config.MAX_CONF_THRESHOLD
                },
                'slice_size': {
                    'min': Config.MIN_SLICE_SIZE,
                    'max': Config.MAX_SLICE_SIZE
                },
                'overlap_ratio': {
                    'min': Config.MIN_OVERLAP_RATIO,
                    'max': Config.MAX_OVERLAP_RATIO
                },
                'match_threshold': {
                    'min': Config.MIN_MATCH_THRESHOLD,
                    'max': Config.MAX_MATCH_THRESHOLD
                }
            },
            'file': {
                'max_size_mb': Config.MAX_CONTENT_LENGTH / (1024 * 1024),
                'allowed_extensions': list(Config.ALLOWED_EXTENSIONS)
            }
        }
        
        return jsonify({
            'success': True,
            'data': config_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Failed to get config: {str(e)}"
        }), 500


@main_bp.route('/cleanup', methods=['POST'])
def cleanup():
    """
    Trigger cleanup of old files.
    
    Returns:
        JSON response with cleanup status
    """
    try:
        file_handler.cleanup_old_files()
        
        return jsonify({
            'success': True,
            'data': {'message': 'Cleanup completed'}
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Cleanup failed: {str(e)}"
        }), 500


@main_bp.route('/system/device', methods=['POST'])
def switch_device():
    """Switch hardware inference device (CPU/GPU)."""
    try:
        data = request.get_json()
        if not data or 'device' not in data:
            return jsonify({'success': False, 'error': 'No device provided, must be cpu or cuda'}), 400
            
        device = data['device']
        result = detection_service.switch_device(device)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Device switch failed: {str(e)}"
        }), 500


# Error handlers
@main_bp.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    max_mb = Config.MAX_CONTENT_LENGTH / (1024 * 1024)
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size: {max_mb}MB'
    }), 413


@main_bp.errorhandler(404)
def not_found(error):
    """Handle not found error."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@main_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server error."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500