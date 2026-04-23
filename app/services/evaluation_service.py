import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
from app.config import Config
from app.services.file_handler import FileHandler

class EvaluationService:
    def __init__(self):
        self.file_handler = FileHandler()

    def get_test_images(self) -> List[str]:
        test_images_dir = Config.BASE_DIR.parent / 'testdata' / 'images'
        if not test_images_dir.exists():
            return []
        
        valid_exts = {'.jpg', '.jpeg', '.png', '.bmp'}
        images = [f.name for f in test_images_dir.iterdir() if f.suffix.lower() in valid_exts]
        return sorted(images)

    def load_ground_truth(self, filename: str) -> List[Dict[str, Any]]:
        labels_dir = Config.BASE_DIR.parent / 'testdata' / 'labels'
        name_stem = Path(filename).stem
        txt_path = labels_dir / f"{name_stem}.txt"
        
        ground_truths = []
        if not txt_path.exists():
            return ground_truths
            
        with open(txt_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    ground_truths.append({
                        'class': class_id,
                        'bbox': [x_center, y_center, width, height] # Normalized YOLO format
                    })
        return ground_truths

    def render_ground_truth(self, image_filename: str) -> str:
        """Draws ground truth boxes on the image and returns the output filename"""
        images_dir = Config.BASE_DIR.parent / 'testdata' / 'images'
        img_path = images_dir / image_filename
        
        if not img_path.exists():
            raise FileNotFoundError(f"Image {image_filename} not found in testdata")
            
        image = cv2.imread(str(img_path))
        if image is None:
            raise RuntimeError(f"Could not load image {image_filename}")
            
        h, w = image.shape[:2]
        gts = self.load_ground_truth(image_filename)
        
        for gt in gts:
            cls_id = gt['class']
            nx, ny, nw, nh = gt['bbox']
            
            # Un-normalize
            x_center = int(nx * w)
            y_center = int(ny * h)
            box_w = int(nw * w)
            box_h = int(nh * h)
            
            x1 = int(x_center - box_w / 2)
            y1 = int(y_center - box_h / 2)
            x2 = int(x_center + box_w / 2)
            y2 = int(y_center + box_h / 2)
            
            color = Config.CLASS_COLORS.get(cls_id, (255, 255, 255))
            label = Config.CLASS_NAMES.get(cls_id, f"Class {cls_id}") + " [GT]"
            
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Label
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
            
            cv2.rectangle(image, (x1, y1 - text_size[1] - 5), (x1 + text_size[0], y1), color, -1)
            cv2.putText(image, label, (x1, y1 - 5), font, font_scale, (0, 0, 0), thickness)
            
        output_filename = f"GT_{image_filename}"
        self.file_handler.save_image(image, output_filename)
        return output_filename

    def _calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """Calculate IoU between two unnormalized boxes [x1, y1, x2, y2]"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        x_left = max(x1_1, x1_2)
        y_top = max(y1_1, y1_2)
        x_right = min(x2_1, x2_2)
        y_bottom = min(y2_1, y2_2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
            
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        
        iou = intersection_area / float(box1_area + box2_area - intersection_area)
        return iou

    def calculate_metrics(self, ground_truths: List[Dict], predictions: Dict, img_w: int, img_h: int) -> Dict[str, Any]:
        """
        Calculates Precision, Recall, F1, mAP@50, mAP@50-95 for a single image.
        """
        if not ground_truths and not predictions.get('boxes', []):
             return {
                 "Precision": 1.0, "Recall": 1.0, "F1-Score": 1.0, 
                 "mAP@50": 1.0, "mAP@50-95": 1.0
             }
        if not ground_truths and predictions.get('boxes', []):
             return {
                 "Precision": 0.0, "Recall": 0.0, "F1-Score": 0.0, 
                 "mAP@50": 0.0, "mAP@50-95": 0.0
             }
        
        # Format GTs into unnormalized [x1, y1, x2, y2]
        gts_by_class = {}
        for gt in ground_truths:
            cls_id = gt['class']
            nx, ny, nw, nh = gt['bbox']
            x1 = (nx - nw/2) * img_w
            y1 = (ny - nh/2) * img_h
            x2 = (nx + nw/2) * img_w
            y2 = (ny + nh/2) * img_h
            if cls_id not in gts_by_class:
                gts_by_class[cls_id] = []
            gts_by_class[cls_id].append([x1, y1, x2, y2])
            
        # Format Predictions
        preds_by_class = {}
        boxes = predictions.get('boxes', [])
        scores = predictions.get('scores', [])
        classes = predictions.get('classes', [])
        
        for i in range(len(boxes)):
            cls_id = classes[i]
            if cls_id not in preds_by_class:
                preds_by_class[cls_id] = []
            preds_by_class[cls_id].append({
                'box': boxes[i],
                'score': scores[i]
            })
            
        all_classes = set(gts_by_class.keys()).union(set(preds_by_class.keys()))
        
        total_tp = 0
        total_fp = 0
        total_gt = sum(len(gts) for gts in gts_by_class.values())
        
        aps_50 = []
        aps_50_95 = []
        
        iou_thresholds = np.linspace(0.5, 0.95, 10)
        
        for cls_id in all_classes:
            gts = gts_by_class.get(cls_id, [])
            preds = preds_by_class.get(cls_id, [])
            
            # Sort preds by score descending
            preds.sort(key=lambda x: x['score'], reverse=True)
            
            # Base precision/recall calculation at IoU=0.5
            tp_array = np.zeros(len(preds))
            fp_array = np.zeros(len(preds))
            
            # For multiple thresholds
            tps_thresholds = np.zeros((len(preds), len(iou_thresholds)))
            fps_thresholds = np.zeros((len(preds), len(iou_thresholds)))
            
            matched_gts_per_thresh = {th: set() for th in iou_thresholds}
            
            for p_idx, p in enumerate(preds):
                best_iou = 0
                best_gt_idx = -1
                for g_idx, g in enumerate(gts):
                    iou = self._calculate_iou(p['box'], g)
                    if iou > best_iou:
                        best_iou = iou
                        best_gt_idx = g_idx
                
                # Check against all thresholds
                for t_idx, th in enumerate(iou_thresholds):
                    if best_iou >= th and best_gt_idx not in matched_gts_per_thresh[th]:
                        tps_thresholds[p_idx, t_idx] = 1
                        matched_gts_per_thresh[th].add(best_gt_idx)
                    else:
                        fps_thresholds[p_idx, t_idx] = 1
            
            # AP calculation per threshold
            ap_thresholds = []
            for t_idx, th in enumerate(iou_thresholds):
                tps_cum = np.cumsum(tps_thresholds[:, t_idx])
                fps_cum = np.cumsum(fps_thresholds[:, t_idx])
                
                recalls = tps_cum / len(gts) if len(gts) > 0 else np.zeros_like(tps_cum)
                precisions = tps_cum / (tps_cum + fps_cum)
                
                # If no ground truth but we have predictions, precision is 0, recall is 0, AP is 0
                if len(gts) == 0:
                    ap_thresholds.append(0.0)
                    continue
                
                # Compute AP using 11-point interpolation or area under curve
                # Here we use basic interpolation
                ap = 0.0
                for r in np.arange(0.0, 1.1, 0.1):
                    mask = recalls >= r
                    if np.any(mask):
                        ap += np.max(precisions[mask]) / 11.0
                ap_thresholds.append(ap)
            
            if len(gts) > 0 or len(preds) > 0:
                aps_50.append(ap_thresholds[0])
                aps_50_95.append(np.mean(ap_thresholds))
            
            # For overall Precision, Recall (at IoU 0.5)
            total_tp += np.sum(tps_thresholds[:, 0])
            total_fp += np.sum(fps_thresholds[:, 0])
            
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        recall = total_tp / total_gt if total_gt > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        map50 = np.mean(aps_50) if aps_50 else 0.0
        map50_95 = np.mean(aps_50_95) if aps_50_95 else 0.0
        
        return {
            "Precision": f"{precision:.3f}",
            "Recall": f"{recall:.3f}",
            "F1-Score": f"{f1:.3f}",
            "mAP@50": f"{map50:.3f}",
            "mAP@50-95": f"{map50_95:.3f}"
        }

    def calculate_batch_metrics(self, ground_truths_list: List[List[Dict]], predictions_list: List[Dict], img_dims_list: List[Tuple[int, int]]) -> Dict[str, Any]:
        """
        Calculates Precision, Recall, F1, mAP@50, mAP@50-95 for a batch of images.
        """
        if not ground_truths_list and not any(p.get('boxes') for p in predictions_list):
             return {
                 "Precision": 1.0, "Recall": 1.0, "F1-Score": 1.0, 
                 "mAP@50": 1.0, "mAP@50-95": 1.0
             }
        
        gts_by_class = {}
        preds_by_class = {}
        
        total_gt = 0
        img_idx_offset = 0 # To track which image a prediction belongs to
        
        for img_idx, (ground_truths, predictions, (img_w, img_h)) in enumerate(zip(ground_truths_list, predictions_list, img_dims_list)):
            # Format GTs
            for gt in ground_truths:
                cls_id = gt['class']
                nx, ny, nw, nh = gt['bbox']
                x1 = (nx - nw/2) * img_w
                y1 = (ny - nh/2) * img_h
                x2 = (nx + nw/2) * img_w
                y2 = (ny + nh/2) * img_h
                if cls_id not in gts_by_class:
                    gts_by_class[cls_id] = []
                gts_by_class[cls_id].append({'box': [x1, y1, x2, y2], 'img_idx': img_idx})
                total_gt += 1
                
            # Format Predictions
            boxes = predictions.get('boxes', [])
            scores = predictions.get('scores', [])
            classes = predictions.get('classes', [])
            
            for i in range(len(boxes)):
                cls_id = classes[i]
                if cls_id not in preds_by_class:
                    preds_by_class[cls_id] = []
                preds_by_class[cls_id].append({
                    'box': boxes[i],
                    'score': scores[i],
                    'img_idx': img_idx
                })
                
        all_classes = set(gts_by_class.keys()).union(set(preds_by_class.keys()))
        
        total_tp = 0
        total_fp = 0
        
        aps_50 = []
        aps_50_95 = []
        
        iou_thresholds = np.linspace(0.5, 0.95, 10)
        
        for cls_id in all_classes:
            gts = gts_by_class.get(cls_id, [])
            preds = preds_by_class.get(cls_id, [])
            
            # Sort preds by score descending globally
            preds.sort(key=lambda x: x['score'], reverse=True)
            
            tps_thresholds = np.zeros((len(preds), len(iou_thresholds)))
            fps_thresholds = np.zeros((len(preds), len(iou_thresholds)))
            
            matched_gts_per_thresh = {th: set() for th in iou_thresholds} # Store matched gt by (th, img_idx, gt_idx)
            
            # Organize GTs by image index for faster lookup
            gts_by_img = {}
            for g_idx, g in enumerate(gts):
                img_idx = g['img_idx']
                if img_idx not in gts_by_img:
                    gts_by_img[img_idx] = []
                gts_by_img[img_idx].append((g_idx, g['box']))
            
            for p_idx, p in enumerate(preds):
                img_idx = p['img_idx']
                p_box = p['box']
                img_gts = gts_by_img.get(img_idx, [])
                
                best_iou = 0
                best_gt_idx = -1
                for global_g_idx, g_box in img_gts:
                    iou = self._calculate_iou(p_box, g_box)
                    if iou > best_iou:
                        best_iou = iou
                        best_gt_idx = global_g_idx
                
                # Check against all thresholds
                for t_idx, th in enumerate(iou_thresholds):
                    if best_iou >= th and best_gt_idx not in matched_gts_per_thresh[th]:
                        tps_thresholds[p_idx, t_idx] = 1
                        matched_gts_per_thresh[th].add(best_gt_idx)
                    else:
                        fps_thresholds[p_idx, t_idx] = 1
            
            # AP calculation per threshold
            ap_thresholds = []
            for t_idx, th in enumerate(iou_thresholds):
                tps_cum = np.cumsum(tps_thresholds[:, t_idx])
                fps_cum = np.cumsum(fps_thresholds[:, t_idx])
                
                recalls = tps_cum / len(gts) if len(gts) > 0 else np.zeros_like(tps_cum)
                precisions = tps_cum / (tps_cum + fps_cum)
                
                if len(gts) == 0:
                    ap_thresholds.append(0.0)
                    continue
                
                ap = 0.0
                for r in np.arange(0.0, 1.1, 0.1):
                    mask = recalls >= r
                    if np.any(mask):
                        ap += np.max(precisions[mask]) / 11.0
                ap_thresholds.append(ap)
            
            if len(gts) > 0 or len(preds) > 0:
                aps_50.append(ap_thresholds[0])
                aps_50_95.append(np.mean(ap_thresholds))
            
            total_tp += np.sum(tps_thresholds[:, 0])
            total_fp += np.sum(fps_thresholds[:, 0])
            
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        recall = total_tp / total_gt if total_gt > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        map50 = np.mean(aps_50) if aps_50 else 0.0
        map50_95 = np.mean(aps_50_95) if aps_50_95 else 0.0
        
        return {
            "Precision": f"{precision:.3f}",
            "Recall": f"{recall:.3f}",
            "F1-Score": f"{f1:.3f}",
            "mAP@50": f"{map50:.3f}",
            "mAP@50-95": f"{map50_95:.3f}"
        }
