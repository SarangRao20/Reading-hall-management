#!/usr/bin/env python3
"""
Camera utilities for SudarshanView computer vision system
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Union
import time

class CameraManager:
    """Manages camera operations and settings"""
    
    def __init__(self, camera_source: Union[int, str] = 0):
        self.camera_source = camera_source
        self.cap = None
        self.is_opened = False
        self.frame_count = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
    def initialize_camera(self, width: int = 800, height: int = 600) -> bool:
        """Initialize camera with specified resolution"""
        try:
            self.cap = cv2.VideoCapture(self.camera_source)
            
            if not self.cap.isOpened():
                print(f"Error: Could not open camera {self.camera_source}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            print(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            self.is_opened = True
            return True
            
        except Exception as e:
            print(f"Error initializing camera: {e}")
            return False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a frame from camera"""
        if not self.is_opened or self.cap is None:
            return False, None
        
        ret, frame = self.cap.read()
        
        if ret:
            self.frame_count += 1
            self._update_fps()
            
        return ret, frame
    
    def _update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_start_time >= 1.0:  # Update every second
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def get_camera_info(self) -> dict:
        """Get camera information"""
        if not self.is_opened or self.cap is None:
            return {}
        
        return {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.cap.get(cv2.CAP_PROP_FPS)),
            'current_fps': self.current_fps,
            'frame_count': self.frame_count,
            'brightness': self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            'contrast': self.cap.get(cv2.CAP_PROP_CONTRAST),
            'saturation': self.cap.get(cv2.CAP_PROP_SATURATION),
            'hue': self.cap.get(cv2.CAP_PROP_HUE)
        }
    
    def set_camera_property(self, property_id: int, value: float) -> bool:
        """Set camera property"""
        if not self.is_opened or self.cap is None:
            return False
        
        return self.cap.set(property_id, value)
    
    def auto_adjust_camera(self) -> dict:
        """Automatically adjust camera settings for optimal detection"""
        adjustments = {}
        
        if not self.is_opened:
            return adjustments
        
        try:
            # Read a few frames to get current exposure
            frames = []
            for _ in range(5):
                ret, frame = self.read_frame()
                if ret:
                    frames.append(frame)
                time.sleep(0.1)
            
            if not frames:
                return adjustments
            
            # Calculate average brightness
            avg_frame = np.mean(frames, axis=0).astype(np.uint8)
            avg_brightness = np.mean(cv2.cvtColor(avg_frame, cv2.COLOR_BGR2GRAY))
            
            adjustments['original_brightness'] = avg_brightness
            
            # Adjust exposure/brightness if too dark or too bright
            if avg_brightness < 80:  # Too dark
                self.set_camera_property(cv2.CAP_PROP_BRIGHTNESS, 0.6)
                self.set_camera_property(cv2.CAP_PROP_EXPOSURE, -1)
                adjustments['brightness_adjusted'] = 'increased'
            elif avg_brightness > 180:  # Too bright
                self.set_camera_property(cv2.CAP_PROP_BRIGHTNESS, 0.4)
                self.set_camera_property(cv2.CAP_PROP_EXPOSURE, -3)
                adjustments['brightness_adjusted'] = 'decreased'
            
            # Optimize contrast for better edge detection
            self.set_camera_property(cv2.CAP_PROP_CONTRAST, 0.7)
            adjustments['contrast_set'] = 0.7
            
            # Slightly increase saturation for better color detection
            self.set_camera_property(cv2.CAP_PROP_SATURATION, 0.6)
            adjustments['saturation_set'] = 0.6
            
        except Exception as e:
            adjustments['error'] = str(e)
        
        return adjustments
    
    def release(self):
        """Release camera resources"""
        if self.cap is not None:
            self.cap.release()
            self.is_opened = False
        cv2.destroyAllWindows()

def test_cameras() -> dict:
    """Test available cameras and return information"""
    available_cameras = {}
    
    for i in range(5):  # Test first 5 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            # Try to read a frame
            ret, frame = cap.read()
            
            available_cameras[i] = {
                'width': width,
                'height': height,
                'fps': fps,
                'working': ret,
                'backend': cap.getBackendName() if hasattr(cap, 'getBackendName') else 'unknown'
            }
            
            cap.release()
    
    return available_cameras

def create_test_pattern(width: int = 800, height: int = 600) -> np.ndarray:
    """Create a test pattern for development/testing"""
    # Create a gradient background
    test_frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add gradient
    for y in range(height):
        intensity = int(255 * y / height)
        test_frame[y, :] = [intensity // 3, intensity // 2, intensity]
    
    # Add grid pattern
    grid_size = 50
    for x in range(0, width, grid_size):
        cv2.line(test_frame, (x, 0), (x, height), (100, 100, 100), 1)
    for y in range(0, height, grid_size):
        cv2.line(test_frame, (0, y), (width, y), (100, 100, 100), 1)
    
    # Add some test "seats"
    seat_positions = [
        (100, 100), (200, 100), (300, 100), (400, 100), (500, 100),
        (100, 200), (200, 200), (300, 200), (400, 200), (500, 200),
        (100, 300), (200, 300), (300, 300), (400, 300), (500, 300)
    ]
    
    for i, (x, y) in enumerate(seat_positions):
        # Simulate occupied (red) or empty (green) seats
        color = (0, 0, 255) if i % 3 == 0 else (0, 255, 0)
        cv2.circle(test_frame, (x, y), 20, color, -1)
        cv2.putText(test_frame, f'S{i+1}', (x-10, y+5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    # Add timestamp
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(test_frame, f"Test Pattern - {timestamp}", (10, height-20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return test_frame

class FrameBuffer:
    """Buffer for storing recent frames"""
    
    def __init__(self, max_size: int = 30):
        self.max_size = max_size
        self.frames = []
        self.timestamps = []
    
    def add_frame(self, frame: np.ndarray):
        """Add frame to buffer"""
        current_time = time.time()
        
        if len(self.frames) >= self.max_size:
            self.frames.pop(0)
            self.timestamps.pop(0)
        
        self.frames.append(frame.copy())
        self.timestamps.append(current_time)
    
    def get_frame(self, index: int = -1) -> Optional[np.ndarray]:
        """Get frame by index (default: latest)"""
        if not self.frames:
            return None
        
        try:
            return self.frames[index].copy()
        except IndexError:
            return None
    
    def get_frame_by_time(self, seconds_ago: float) -> Optional[np.ndarray]:
        """Get frame from specified seconds ago"""
        if not self.frames:
            return None
        
        target_time = time.time() - seconds_ago
        
        # Find closest frame
        closest_index = 0
        min_diff = abs(self.timestamps[0] - target_time)
        
        for i, timestamp in enumerate(self.timestamps):
            diff = abs(timestamp - target_time)
            if diff < min_diff:
                min_diff = diff
                closest_index = i
        
        return self.frames[closest_index].copy()
    
    def get_average_frame(self, num_frames: int = 5) -> Optional[np.ndarray]:
        """Get average of recent frames"""
        if len(self.frames) < num_frames:
            num_frames = len(self.frames)
        
        if num_frames == 0:
            return None
        
        recent_frames = self.frames[-num_frames:]
        avg_frame = np.mean(recent_frames, axis=0).astype(np.uint8)
        
        return avg_frame
    
    def clear(self):
        """Clear buffer"""
        self.frames.clear()
        self.timestamps.clear()

def main():
    """Test camera utilities"""
    print("Testing available cameras...")
    cameras = test_cameras()
    
    if not cameras:
        print("No cameras found!")
        return
    
    print("Available cameras:")
    for cam_id, info in cameras.items():
        print(f"  Camera {cam_id}: {info['width']}x{info['height']} @ {info['fps']}fps - {'Working' if info['working'] else 'Not working'}")
    
    # Test camera manager with first available camera
    first_cam = min(cameras.keys())
    print(f"\nTesting Camera Manager with camera {first_cam}...")
    
    camera = CameraManager(first_cam)
    if camera.initialize_camera():
        print("Camera initialized successfully!")
        
        # Test frame reading
        for i in range(10):
            ret, frame = camera.read_frame()
            if ret:
                print(f"Frame {i+1}: {frame.shape}")
            else:
                print(f"Failed to read frame {i+1}")
            time.sleep(0.1)
        
        # Show camera info
        info = camera.get_camera_info()
        print(f"Camera info: {info}")
        
        camera.release()
    else:
        print("Failed to initialize camera!")

if __name__ == "__main__":
    main()
