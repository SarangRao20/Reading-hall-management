#!/usr/bin/env python3
"""
SudarshanView Computer Vision Demo
A simple demo to test the computer vision system
"""

import cv2
import numpy as np
import sys
import os
import time
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from computer_vision.utils.camera_utils import CameraManager, create_test_pattern
    from computer_vision.utils.image_utils import draw_seat_overlay, enhance_frame
except ImportError:
    print("Could not import utilities. Running basic demo...")
    CameraManager = None

def create_demo_seats():
    """Create demo seat positions"""
    seats = []
    seat_id = 1
    
    # Create 5 rows x 10 columns of seats
    for row in range(5):
        for col in range(10):
            seats.append({
                'id': seat_id,
                'seat_number': f"R{row+1}S{col+1}",
                'position_x': 80 + col * 70,
                'position_y': 100 + row * 80,
                'hall_id': 1
            })
            seat_id += 1
    
    return seats

def basic_demo():
    """Basic OpenCV demo without utilities"""
    print("🎥 SudarshanView Computer Vision Demo")
    print("=====================================")
    print("Running basic demo...")
    
    # Try to open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Camera not found. Creating test pattern...")
        # Create a test pattern
        test_frame = create_test_pattern_basic()
        
        print("📺 Displaying test pattern...")
        print("Press 'q' to quit, 's' to save screenshot")
        
        while True:
            # Add some animation
            timestamp = datetime.now().strftime("%H:%M:%S")
            frame = test_frame.copy()
            cv2.putText(frame, timestamp, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            cv2.imshow('SudarshanView Demo - Test Pattern', frame)
            
            key = cv2.waitKey(1000) & 0xFF  # Update every second
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f"demo_screenshot_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"💾 Screenshot saved: {filename}")
        
        cv2.destroyAllWindows()
        return
    
    print("✅ Camera found! Starting live demo...")
    print("Press 'q' to quit, 's' to save screenshot, 'd' for detection mode")
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
    
    detection_mode = False
    seats = create_demo_seats()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read frame")
            break
        
        # Add overlay information
        overlay_frame = frame.copy()
        
        # Add title
        cv2.putText(overlay_frame, "SudarshanView Demo", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(overlay_frame, timestamp, (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        if detection_mode:
            # Draw seat positions
            for seat in seats[:15]:  # Show first 15 seats
                x, y = seat['position_x'], seat['position_y']
                
                # Make sure coordinates are within frame
                if 0 < x < frame.shape[1] and 0 < y < frame.shape[0]:
                    # Simulate random occupancy
                    is_occupied = (int(time.time()) + seat['id']) % 4 == 0
                    color = (0, 0, 255) if is_occupied else (0, 255, 0)
                    
                    cv2.circle(overlay_frame, (x, y), 15, color, 2)
                    cv2.putText(overlay_frame, seat['seat_number'], (x-20, y-25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
            
            cv2.putText(overlay_frame, "Detection Mode ON", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(overlay_frame, "Live Camera Feed", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add instructions
        cv2.putText(overlay_frame, "Controls: Q=Quit, S=Save, D=Detection", 
                   (10, overlay_frame.shape[0]-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        cv2.imshow('SudarshanView Computer Vision Demo', overlay_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"demo_screenshot_{int(time.time())}.jpg"
            cv2.imwrite(filename, overlay_frame)
            print(f"💾 Screenshot saved: {filename}")
        elif key == ord('d'):
            detection_mode = not detection_mode
            mode_text = "ON" if detection_mode else "OFF"
            print(f"🔍 Detection mode: {mode_text}")
    
    cap.release()
    cv2.destroyAllWindows()

def advanced_demo():
    """Advanced demo using utilities"""
    print("🎥 SudarshanView Computer Vision Demo (Advanced)")
    print("==============================================")
    
    # Initialize camera manager
    camera = CameraManager(0)
    
    if not camera.initialize_camera():
        print("❌ Failed to initialize camera. Using test pattern...")
        # Show test pattern
        test_frame = create_test_pattern()
        
        while True:
            cv2.imshow('SudarshanView Advanced Demo - Test Pattern', test_frame)
            if cv2.waitKey(1000) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()
        return
    
    print("✅ Camera initialized successfully!")
    
    # Auto-adjust camera settings
    adjustments = camera.auto_adjust_camera()
    print(f"📸 Camera adjustments: {adjustments}")
    
    seats = create_demo_seats()
    occupied_seats = set()
    
    print("🔍 Starting advanced detection...")
    print("Controls: Q=Quit, S=Save, Space=Toggle occupancy")
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = camera.read_frame()
            if not ret:
                print("❌ Failed to read frame")
                break
            
            frame_count += 1
            
            # Enhance frame
            enhanced_frame = enhance_frame(frame)
            
            # Draw seat overlay
            display_frame = draw_seat_overlay(enhanced_frame, seats, occupied_seats)
            
            # Add information overlay
            info = camera.get_camera_info()
            cv2.putText(display_frame, f"FPS: {info.get('current_fps', 0)}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(display_frame, f"Frame: {frame_count}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(display_frame, f"Occupied: {len(occupied_seats)}/{len(seats)}", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Simulate occupancy changes
            if frame_count % 60 == 0:  # Every 60 frames (~2 seconds)
                # Randomly toggle some seats
                import random
                for _ in range(random.randint(1, 3)):
                    seat_id = random.choice(seats)['id']
                    if seat_id in occupied_seats:
                        occupied_seats.remove(seat_id)
                    else:
                        occupied_seats.add(seat_id)
            
            cv2.imshow('SudarshanView Advanced Demo', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f"advanced_demo_{int(time.time())}.jpg"
                cv2.imwrite(filename, display_frame)
                print(f"💾 Screenshot saved: {filename}")
            elif key == ord(' '):  # Space bar
                # Toggle random seat
                import random
                seat_id = random.choice(seats)['id']
                if seat_id in occupied_seats:
                    occupied_seats.remove(seat_id)
                    print(f"🟢 Seat {seat_id} freed")
                else:
                    occupied_seats.add(seat_id)
                    print(f"🔴 Seat {seat_id} occupied")
    
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    
    finally:
        camera.release()
        print("🔚 Demo completed")

def create_test_pattern_basic(width=800, height=600):
    """Create a basic test pattern"""
    # Create gradient background
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add gradient
    for y in range(height):
        intensity = int(255 * y / height)
        frame[y, :] = [intensity // 3, intensity // 2, intensity]
    
    # Add title
    cv2.putText(frame, "SudarshanView Demo", (width//2-150, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    
    # Add some demo seats
    for i in range(15):
        x = 100 + (i % 5) * 120
        y = 150 + (i // 5) * 100
        
        # Alternate colors to simulate occupancy
        color = (0, 0, 255) if i % 3 == 0 else (0, 255, 0)
        
        cv2.circle(frame, (x, y), 20, color, -1)
        cv2.putText(frame, f'S{i+1}', (x-10, y+5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    # Add legend
    cv2.rectangle(frame, (50, height-120), (300, height-20), (50, 50, 50), -1)
    cv2.putText(frame, "Legend:", (60, height-100), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.circle(frame, (80, height-70), 10, (0, 255, 0), -1)
    cv2.putText(frame, "Available", (100, height-65), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.circle(frame, (80, height-40), 10, (0, 0, 255), -1)
    cv2.putText(frame, "Occupied", (100, height-35), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return frame

def main():
    """Main demo function"""
    print("🪑 SudarshanView Computer Vision System")
    print("====================================")
    print("Choose demo mode:")
    print("1. Basic Demo (simple OpenCV)")
    print("2. Advanced Demo (with utilities)")
    print("3. Test Camera")
    print("4. Exit")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            basic_demo()
        elif choice == '2':
            if CameraManager:
                advanced_demo()
            else:
                print("❌ Utilities not available. Running basic demo...")
                basic_demo()
        elif choice == '3':
            test_camera()
        elif choice == '4':
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_camera():
    """Test camera functionality"""
    print("🔧 Testing camera...")
    
    if CameraManager:
        from computer_vision.utils.camera_utils import test_cameras
        cameras = test_cameras()
        
        print(f"📷 Found {len(cameras)} cameras:")
        for cam_id, info in cameras.items():
            status = "✅ Working" if info['working'] else "❌ Not working"
            print(f"  Camera {cam_id}: {info['width']}x{info['height']} @ {info['fps']}fps - {status}")
    else:
        print("Testing basic camera access...")
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"✅ Camera {i}: Available")
                cap.release()
            else:
                print(f"❌ Camera {i}: Not available")

if __name__ == "__main__":
    main()
