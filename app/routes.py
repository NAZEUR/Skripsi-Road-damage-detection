"""
Flask Routes
API endpoints for the road damage detection application.
"""
from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import os
import logging
from app.config import Config
from app.services import DetectionService, FileHandler
from app.utils import ParameterValidator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info("Detection request received")
        
        # Get request data
        data = request.get_json()
        
        if not data:
            logger.warning("No data provided in detection request")
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        if 'filepath' not in data:
            logger.warning("filepath not provided in detection request")
            return jsonify({
                'success': False,
                'error': 'filepath is required'
            }), 400
        
        if 'mode' not in data:
            logger.warning("mode not provided in detection request")
            return jsonify({
                'success': False,
                'error': 'mode is required (baseline or sahi)'
            }), 400
        
        # Extract parameters
        filepath = data['filepath']
        mode = data['mode']
        confidence = data.get('confidence', Config.DEFAULT_CONF_THRESHOLD)
        
        logger.info(f"Detection started for {filepath} using mode: {mode} with confidence: {confidence}")
        
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
            logger.warning(f"Parameter validation failed: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        # Perform detection
        logger.info("Starting detection processing...")
        result = detection_service.process_detection(
            image_path=filepath,
            mode=mode,
            **detect_params
        )
        logger.info(f"Detection completed. Found {result['detections']['count']} detections")
        
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
        logger.error(f"ValueError in detection: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        # Server error
        logger.error(f"Exception in detection: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
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



@main_bp.route('/zip_results', methods=['POST'])
def zip_results():
    try:
        data = request.json
        if not data or 'files' not in data:
            return jsonify({'success': False, 'error': 'No files specified'}), 400
            
        filenames = data['files']
        if not filenames:
            return jsonify({'success': False, 'error': 'Empty files list'}), 400
            
        import io
        import zipfile
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename in filenames:
                file_path = Config.OUTPUT_FOLDER / filename
                if file_path.exists():
                    zf.write(str(file_path), filename)
                    
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='results_archive.zip'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

from flask import render_template

@main_bp.route('/statistics', methods=['GET'])
def statistics():
    return render_template('statistics.html')


from app.services.evaluation_service import EvaluationService
eval_service = EvaluationService()

@main_bp.route('/evaluate', methods=['GET'])
def evaluate_page():
    return render_template('evaluate.html')

@main_bp.route('/api/test_images', methods=['GET'])
def api_test_images():
    try:
        images = eval_service.get_test_images()
        return jsonify({'success': True, 'data': images}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/evaluate_single', methods=['POST'])
def api_evaluate_single():
    try:
        data = request.json
        filename = data.get('filename')
        if not filename:
            return jsonify({'success': False, 'error': 'No filename provided'}), 400
            
        conf_threshold = data.get('confidence', Config.DEFAULT_CONF_THRESHOLD)
        slice_height = data.get('slice_height', Config.DEFAULT_SLICE_HEIGHT)
        slice_width = data.get('slice_width', Config.DEFAULT_SLICE_WIDTH)
        overlap_ratio = data.get('overlap_ratio', Config.DEFAULT_OVERLAP_RATIO)
        match_threshold = data.get('match_threshold', Config.DEFAULT_MATCH_THRESHOLD)
        
        # Paths
        images_dir = Config.BASE_DIR.parent / 'testdata' / 'images'
        img_path = images_dir / filename
        
        if not img_path.exists():
            return jsonify({'success': False, 'error': 'Image not found'}), 404
            
        import time
        
        # 1. Ground Truth
        gt_filename = eval_service.render_ground_truth(filename)
        gts = eval_service.load_ground_truth(filename)
        
        import cv2
        img = cv2.imread(str(img_path))
        img_h, img_w = img.shape[:2]
        
        # 2. Baseline YOLO
        start_t = time.time()
        baseline_res = detection_service.detect_baseline(str(img_path), conf_threshold)
        baseline_time = time.time() - start_t
        
        baseline_filename = f"baseline_{filename}"
        detection_service.visualizer.save_visualization(img, baseline_res, Config.OUTPUT_FOLDER / baseline_filename)
        baseline_metrics = eval_service.calculate_metrics(gts, baseline_res, img_w, img_h)
        baseline_metrics['Eval Time'] = f"{baseline_time*1000:.0f} ms"
        
        # 3. SAHI
        start_t = time.time()
        sahi_res = detection_service.detect_sahi(
            str(img_path), 
            slice_height=slice_height, slice_width=slice_width, 
            overlap_ratio=overlap_ratio, match_threshold=match_threshold, conf_threshold=conf_threshold
        )
        sahi_time = time.time() - start_t
        
        sahi_filename = f"sahi_{filename}"
        detection_service.visualizer.save_visualization(img, sahi_res, Config.OUTPUT_FOLDER / sahi_filename)
        sahi_metrics = eval_service.calculate_metrics(gts, sahi_res, img_w, img_h)
        sahi_metrics['Eval Time'] = f"{sahi_time*1000:.0f} ms"
        
        return jsonify({
            'success': True,
            'data': {
                'original': f"/api/raw_test_image/{filename}",
                'gt_image': f"/view/{gt_filename}",
                'baseline_image': f"/view/{baseline_filename}",
                'sahi_image': f"/view/{sahi_filename}",
                'baseline_metrics': baseline_metrics,
                'sahi_metrics': sahi_metrics
            }
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/raw_test_image/<filename>', methods=['GET'])
def api_raw_test_image(filename):
    try:
        images_dir = Config.BASE_DIR.parent / 'testdata' / 'images'
        file_path = images_dir / filename
        if not file_path.exists():
            return jsonify({'success': False, 'error': 'File not found'}), 404
        return send_file(str(file_path), mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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