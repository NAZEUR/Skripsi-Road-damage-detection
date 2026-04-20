import re

with open(r"app\routes.py", "r", encoding="utf-8") as f:
    code = f.read()

new_routes = """
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
        detection_service.visualizer.visualize(img, baseline_res['detections'], Config.OUTPUT_FOLDER / baseline_filename)
        baseline_metrics = eval_service.calculate_metrics(gts, baseline_res['detections'], img_w, img_h)
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
        detection_service.visualizer.visualize(img, sahi_res['detections'], Config.OUTPUT_FOLDER / sahi_filename)
        sahi_metrics = eval_service.calculate_metrics(gts, sahi_res['detections'], img_w, img_h)
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
"""

code = code.replace("# Error handlers\n", new_routes)

with open(r"app\routes.py", "w", encoding="utf-8") as f:
    f.write(code)
