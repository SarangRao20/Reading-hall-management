#!/usr/bin/env python3
"""
Image processing utilities for SudarshanView computer vision
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional
import os
from datetime import datetime

def resize_frame(frame: np.ndarray, target_width: int = 800, target_height: int = 600) -> np.ndarray:
    """Resize frame to target dimensions"""
    return cv2.resize(frame, (target_width, target_height))

def enhance_frame(frame: np.ndarray) -> np.ndarray:
    """Enhance frame for better detection"""
    # Convert to LAB color space for better lighting normalization
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    
    # Merge channels and convert back to BGR
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    return enhanced

def create_roi_mask(frame_shape: Tuple[int, int], seats: List[dict], roi_size: int = 40) -> np.ndarray:
    """Create a mask for regions of interest (seat areas)"""
    mask = np.zeros(frame_shape[:2], dtype=np.uint8)
    
    for seat in seats:
        x, y = seat['position_x'], seat['position_y']
        x1 = max(0, x - roi_size)
        y1 = max(0, y - roi_size)
        x2 = min(frame_shape[1], x + roi_size)
        y2 = min(frame_shape[0], y + roi_size)
        
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
    
    return mask

def draw_seat_overlay(frame: np.ndarray, seats: List[dict], occupied_seats: set = None) -> np.ndarray:
    """Draw seat positions and status overlay on frame"""
    overlay = frame.copy()
    occupied_seats = occupied_seats or set()
    
    for seat in seats:
        x, y = seat['position_x'], seat['position_y']
        seat_id = seat['id']
        
        # Choose color based on occupancy
        if seat_id in occupied_seats:
            color = (0, 0, 255)  # Red for occupied
            status = "OCCUPIED"
        else:
            color = (0, 255, 0)  # Green for available
            status = "AVAILABLE"
        
        # Draw seat circle
        cv2.circle(overlay, (x, y), 20, color, 2)
        
        # Draw seat number
        cv2.putText(overlay, seat['seat_number'], (x-15, y-25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # Draw status (smaller text)
        cv2.putText(overlay, status, (x-20, y+35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
    
    return overlay

def save_detection_frame(frame: np.ndarray, seat_number: str, is_occupied: bool, 
                        confidence: float, save_dir: str = "detections") -> str:
    """Save frame with detection result"""
    os.makedirs(save_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
    status = "occupied" if is_occupied else "empty"
    filename = f"seat_{seat_number}_{timestamp}_{status}_{confidence:.2f}.jpg"
    filepath = os.path.join(save_dir, filename)
    
    # Add timestamp and info overlay to frame
    overlay_frame = frame.copy()
    cv2.putText(overlay_frame, f"Seat: {seat_number}", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(overlay_frame, f"Status: {status.upper()}", (10, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(overlay_frame, f"Confidence: {confidence:.2f}", (10, 90), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(overlay_frame, timestamp, (10, 120), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.imwrite(filepath, overlay_frame)
    return filepath

def create_detection_grid(detections: List[dict], grid_size: Tuple[int, int] = (5, 10)) -> np.ndarray:
    """Create a visual grid showing all seat detection states"""
    rows, cols = grid_size
    cell_size = 60
    grid_img = np.ones((rows * cell_size, cols * cell_size, 3), dtype=np.uint8) * 50
    
    for i, detection in enumerate(detections[:rows*cols]):
        row = i // cols
        col = i % cols
        
        # Calculate cell position
        y1 = row * cell_size
        x1 = col * cell_size
        y2 = y1 + cell_size
        x2 = x1 + cell_size
        
        # Choose color based on occupancy
        if detection.get('is_occupied', False):
            color = (0, 0, 255)  # Red
        else:
            color = (0, 255, 0)  # Green
        
        # Draw cell
        cv2.rectangle(grid_img, (x1, y1), (x2-1, y2-1), color, 2)
        
        # Add seat number
        seat_num = detection.get('seat_number', f'S{i+1}')
        text_size = cv2.getTextSize(seat_num, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
        text_x = x1 + (cell_size - text_size[0]) // 2
        text_y = y1 + (cell_size + text_size[1]) // 2
        
        cv2.putText(grid_img, seat_num, (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    return grid_img

def calculate_frame_difference(frame1: np.ndarray, frame2: np.ndarray, 
                             threshold: int = 30) -> Tuple[np.ndarray, float]:
    """Calculate difference between two frames"""
    if frame1.shape != frame2.shape:
        frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
    
    # Convert to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY) if len(frame1.shape) == 3 else frame1
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY) if len(frame2.shape) == 3 else frame2
    
    # Calculate absolute difference
    diff = cv2.absdiff(gray1, gray2)
    
    # Apply threshold
    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    
    # Calculate motion percentage
    motion_pixels = cv2.countNonZero(thresh)
    total_pixels = thresh.shape[0] * thresh.shape[1]
    motion_percentage = (motion_pixels / total_pixels) * 100
    
    return thresh, motion_percentage

def create_heatmap(occupancy_data: List[Tuple[int, int, float]], frame_shape: Tuple[int, int]) -> np.ndarray:
    """Create occupancy heatmap"""
    heatmap = np.zeros(frame_shape[:2], dtype=np.float32)
    
    for x, y, intensity in occupancy_data:
        if 0 <= x < frame_shape[1] and 0 <= y < frame_shape[0]:
            # Create gaussian around the point
            gaussian = np.zeros(frame_shape[:2], dtype=np.float32)
            cv2.circle(gaussian, (x, y), 50, intensity, -1)
            
            # Apply gaussian blur
            gaussian = cv2.GaussianBlur(gaussian, (101, 101), 0)
            
            # Add to heatmap
            heatmap = cv2.add(heatmap, gaussian)
    
    # Normalize
    cv2.normalize(heatmap, heatmap, 0, 255, cv2.NORM_MINMAX)
    
    # Convert to color heatmap
    heatmap_colored = cv2.applyColorMap(heatmap.astype(np.uint8), cv2.COLORMAP_JET)
    
    return heatmap_colored

def extract_roi_features(frame: np.ndarray, x: int, y: int, roi_size: int = 40) -> dict:
    """Extract features from a region of interest"""
    # Define ROI bounds
    x1 = max(0, x - roi_size)
    y1 = max(0, y - roi_size)
    x2 = min(frame.shape[1], x + roi_size)
    y2 = min(frame.shape[0], y + roi_size)
    
    if x2 <= x1 or y2 <= y1:
        return {}
    
    roi = frame[y1:y2, x1:x2]
    
    if roi.size == 0:
        return {}
    
    # Convert to different color spaces
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV) if len(roi.shape) == 3 else None
    
    features = {
        'mean_intensity': np.mean(gray),
        'std_intensity': np.std(gray),
        'min_intensity': np.min(gray),
        'max_intensity': np.max(gray),
        'roi_size': roi.shape[0] * roi.shape[1]
    }
    
    if hsv is not None:
        features.update({
            'mean_hue': np.mean(hsv[:, :, 0]),
            'mean_saturation': np.mean(hsv[:, :, 1]),
            'mean_value': np.mean(hsv[:, :, 2])
        })
    
    # Edge detection
    edges = cv2.Canny(gray, 50, 150)
    features['edge_density'] = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
    
    return features
