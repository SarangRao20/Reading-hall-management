#!/usr/bin/env python3
"""
SudarshanView Computer Vision Module
Real-time seat occupancy detection using OpenCV
"""

import cv2
import numpy as np
import requests
import json
import time
import threading
from datetime import datetime
import os
import sqlite3
from typing import List, Tuple, Dict, Optional

class SeatDetector:
    """Computer vision seat detection and occupancy monitoring"""
    
    def __init__(self, config_file='config/vision_config.json'):
        self.config = self.load_config(config_file)
        self.seats = self.load_seat_positions()
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, varThreshold=50
        )
        self.api_url = self.config.get('api_url', 'http://localhost:5000')
        self.camera_url = self.config.get('camera_url', 0)  # 0 for webcam
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.detection_interval = self.config.get('detection_interval', 2)  # seconds
        
        # Initialize YOLO for person detection (optional)
        self.use_yolo = self.config.get('use_yolo', False)
        if self.use_yolo:
            self.init_yolo()
    
    def load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file"""
        default_config = {
            'api_url': 'http://localhost:5000',
            'camera_url': 0,
            'confidence_threshold': 0.7,
            'detection_interval': 2,
            'use_yolo': False,
            'save_detections': True,
            'detection_save_path': 'detections/'
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
        
        return default_config
    
    def load_seat_positions(self) -> List[Dict]:
        """Load seat positions from database"""
        try:
            db_path = os.path.join('..', 'database', 'sudarshanview.db')
            if not os.path.exists(db_path):
                db_path = os.path.join('database', 'sudarshanview.db')
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            seats = conn.execute('''
                SELECT s.id, s.seat_number, s.position_x, s.position_y, s.hall_id,
                       h.name as hall_name
                FROM seats s
                JOIN reading_halls h ON s.hall_id = h.id
                WHERE s.is_available = 1
                ORDER BY s.seat_number
            ''').fetchall()
            
            conn.close()
            
            return [dict(seat) for seat in seats]
        except Exception as e:
            print(f"Error loading seats: {e}")
            return self.get_default_seats()
    
    def get_default_seats(self) -> List[Dict]:
        """Return default seat layout for testing"""
        seats = []
        seat_id = 1
        for row in range(5):
            for col in range(10):
                seats.append({
                    'id': seat_id,
                    'seat_number': f"R{row+1}S{col+1}",
                    'position_x': 50 + col * 70,
                    'position_y': 50 + row * 100,
                    'hall_id': 1,
                    'hall_name': 'Main Reading Hall'
                })
                seat_id += 1
        return seats
    
    def init_yolo(self):
        """Initialize YOLO for person detection"""
        try:
            # Download YOLO files if not exists
            yolo_dir = 'computer_vision/models/yolo'
            os.makedirs(yolo_dir, exist_ok=True)
            
            # You would need to download these files:
            # - yolov3.weights
            # - yolov3.cfg  
            # - coco.names
            
            weights_path = os.path.join(yolo_dir, 'yolov3.weights')
            config_path = os.path.join(yolo_dir, 'yolov3.cfg')
            
            if os.path.exists(weights_path) and os.path.exists(config_path):
                self.net = cv2.dnn.readNet(weights_path, config_path)
                self.layer_names = self.net.getLayerNames()
                self.output_layers = [self.layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
                print("YOLO initialized successfully")
            else:
                print("YOLO files not found, using basic detection")
                self.use_yolo = False
        except Exception as e:
            print(f"Error initializing YOLO: {e}")
            self.use_yolo = False
    
    def detect_persons_yolo(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect persons using YOLO"""
        if not self.use_yolo:
            return []
        
        try:
            height, width, channels = frame.shape
            
            # Detecting objects
            blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
            self.net.setInput(blob)
            outs = self.net.forward(self.output_layers)
            
            # Extract information
            boxes = []
            confidences = []
            class_ids = []
            
            for out in outs:
                for detection in out:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    
                    if class_id == 0 and confidence > self.confidence_threshold:  # class_id 0 is person
                        # Object detected
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        
                        # Rectangle coordinates
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        
                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        class_ids.append(class_id)
            
            # Apply Non-maximum suppression
            indexes = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, 0.4)
            
            persons = []
            if len(indexes) > 0:
                for i in indexes.flatten():
                    x, y, w, h = boxes[i]
                    persons.append((x, y, x + w, y + h))
            
            return persons
        except Exception as e:
            print(f"Error in YOLO detection: {e}")
            return []
    
    def detect_motion_basic(self, frame: np.ndarray) -> np.ndarray:
        """Basic motion detection using background subtraction"""
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(frame)
        
        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        return fg_mask, contours
    
    def is_seat_occupied(self, frame: np.ndarray, seat: Dict) -> Tuple[bool, float]:
        """Determine if a seat is occupied"""
        x, y = seat['position_x'], seat['position_y']
        
        # Define ROI around seat position (adjust size as needed)
        roi_size = 40
        x1 = max(0, x - roi_size)
        y1 = max(0, y - roi_size)
        x2 = min(frame.shape[1], x + roi_size)
        y2 = min(frame.shape[0], y + roi_size)
        
        roi = frame[y1:y2, x1:x2]
        
        if roi.size == 0:
            return False, 0.0
        
        confidence = 0.0
        occupied = False
        
        if self.use_yolo:
            # Use YOLO person detection
            persons = self.detect_persons_yolo(frame)
            for px1, py1, px2, py2 in persons:
                # Check if person overlaps with seat ROI
                if self.rectangles_overlap((x1, y1, x2, y2), (px1, py1, px2, py2)):
                    occupied = True
                    confidence = 0.9
                    break
        else:
            # Use basic motion/color detection
            fg_mask, contours = self.detect_motion_basic(frame)
            
            # Check for motion in seat ROI
            roi_mask = fg_mask[y1:y2, x1:x2]
            motion_pixels = cv2.countNonZero(roi_mask)
            motion_ratio = motion_pixels / (roi_mask.shape[0] * roi_mask.shape[1])
            
            # Check for contours in seat area
            for contour in contours:
                contour_center = self.get_contour_center(contour)
                if contour_center and self.point_in_roi(contour_center, (x1, y1, x2, y2)):
                    area = cv2.contourArea(contour)
                    if area > 500:  # Minimum area threshold
                        occupied = True
                        confidence = min(0.8, motion_ratio * 2 + area / 2000)
                        break
            
            # Additional heuristics can be added here
            # - Color-based detection (chair vs person)
            # - Edge detection
            # - Template matching
        
        return occupied, confidence
    
    def rectangles_overlap(self, rect1: Tuple, rect2: Tuple) -> bool:
        """Check if two rectangles overlap"""
        x1, y1, x2, y2 = rect1
        px1, py1, px2, py2 = rect2
        
        return not (x2 < px1 or px2 < x1 or y2 < py1 or py2 < y1)
    
    def get_contour_center(self, contour) -> Optional[Tuple[int, int]]:
        """Get center point of contour"""
        try:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                return (cx, cy)
        except:
            pass
        return None
    
    def point_in_roi(self, point: Tuple[int, int], roi: Tuple) -> bool:
        """Check if point is inside ROI"""
        px, py = point
        x1, y1, x2, y2 = roi
        return x1 <= px <= x2 and y1 <= py <= y2
    
    def send_detection_to_api(self, seat_id: int, is_occupied: bool, confidence: float, image_path: str = None):
        """Send detection results to backend API"""
        try:
            data = {
                'seat_id': seat_id,
                'is_occupied': is_occupied,
                'confidence': confidence,
                'image_path': image_path
            }
            
            response = requests.post(
                f"{self.api_url}/api/vision/detection",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"Detection sent for seat {seat_id}: occupied={is_occupied}, confidence={confidence:.2f}")
            else:
                print(f"Failed to send detection: {response.status_code}")
        except Exception as e:
            print(f"Error sending detection to API: {e}")
    
    def save_detection_image(self, frame: np.ndarray, seat: Dict, is_occupied: bool, confidence: float) -> Optional[str]:
        """Save detection image for debugging"""
        if not self.config.get('save_detections', False):
            return None
        
        try:
            save_dir = self.config.get('detection_save_path', 'detections/')
            os.makedirs(save_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"seat_{seat['seat_number']}_{timestamp}_{'occupied' if is_occupied else 'empty'}_{confidence:.2f}.jpg"
            filepath = os.path.join(save_dir, filename)
            
            # Draw seat ROI on frame
            x, y = seat['position_x'], seat['position_y']
            roi_size = 40
            cv2.rectangle(frame, (x-roi_size, y-roi_size), (x+roi_size, y+roi_size), (0, 255, 0), 2)
            cv2.putText(frame, seat['seat_number'], (x-roi_size, y-roi_size-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.imwrite(filepath, frame)
            return filepath
        except Exception as e:
            print(f"Error saving detection image: {e}")
            return None
    
    def run_detection(self):
        """Main detection loop"""
        print("Starting seat detection system...")
        print(f"Monitoring {len(self.seats)} seats")
        
        # Initialize camera
        cap = cv2.VideoCapture(self.camera_url)
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        
        last_detection_time = 0
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error reading frame")
                    break
                
                current_time = time.time()
                frame_count += 1
                
                # Run detection at specified interval
                if current_time - last_detection_time >= self.detection_interval:
                    print(f"Processing frame {frame_count}...")
                    
                    for seat in self.seats:
                        is_occupied, confidence = self.is_seat_occupied(frame, seat)
                        
                        if confidence > 0.5:  # Only process confident detections
                            # Save detection image if enabled
                            image_path = self.save_detection_image(frame, seat, is_occupied, confidence)
                            
                            # Send to API
                            self.send_detection_to_api(seat['id'], is_occupied, confidence, image_path)
                    
                    last_detection_time = current_time
                
                # Display frame with seat positions (for debugging)
                if self.config.get('show_video', True):
                    display_frame = frame.copy()
                    for seat in self.seats:
                        x, y = seat['position_x'], seat['position_y']
                        cv2.circle(display_frame, (x, y), 5, (0, 0, 255), -1)
                        cv2.putText(display_frame, seat['seat_number'], (x+10, y), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                    
                    cv2.imshow('SudarshanView - Seat Detection', display_frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        
        except KeyboardInterrupt:
            print("Detection stopped by user")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("Detection system stopped")

def main():
    """Main function"""
    print("SudarshanView Computer Vision System")
    print("===================================")
    
    # Create detector instance
    detector = SeatDetector()
    
    # Start detection
    detector.run_detection()

if __name__ == '__main__':
    main()
