#!/usr/bin/env python3
"""
Barcode Scanner Integration Module
Handles barcode scanning for student ID cards
"""

import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar
import requests
import json
from datetime import datetime
import threading
import time
from typing import Optional, Dict, List

class BarcodeScanner:
    """Barcode scanner for student ID cards"""
    
    def __init__(self, api_url='http://localhost:5000', camera_id=1):
        self.api_url = api_url
        self.camera_id = camera_id
        self.is_scanning = False
        self.last_scanned_code = None
        self.last_scan_time = 0
        self.scan_cooldown = 2  # seconds between same barcode scans
        
    def decode_barcode(self, frame: np.ndarray) -> List[Dict]:
        """Decode barcodes from frame"""
        try:
            # Convert to grayscale for better barcode detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Find barcodes in the frame
            barcodes = pyzbar.decode(gray)
            
            decoded_barcodes = []
            for barcode in barcodes:
                # Extract barcode data and type
                barcode_data = barcode.data.decode('utf-8')
                barcode_type = barcode.type
                
                # Get barcode rectangle
                (x, y, w, h) = barcode.rect
                
                decoded_barcodes.append({
                    'data': barcode_data,
                    'type': barcode_type,
                    'rect': (x, y, w, h),
                    'polygon': barcode.polygon
                })
                
            return decoded_barcodes
            
        except Exception as e:
            print(f"Error decoding barcode: {e}")
            return []
    
    def validate_barcode(self, barcode_data: str) -> Optional[Dict]:
        """Validate barcode with backend API"""
        try:
            response = requests.get(
                f"{self.api_url}/api/users/{barcode_data}",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"Error validating barcode: {e}")
            return None
    
    def check_in_user(self, barcode_data: str, seat_id: int) -> Dict:
        """Check in user using barcode"""
        try:
            data = {
                'barcode': barcode_data,
                'seat_id': seat_id
            }
            
            response = requests.post(
                f"{self.api_url}/api/checkin",
                json=data,
                timeout=5
            )
            
            return {
                'success': response.status_code == 201,
                'data': response.json(),
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    def check_out_user(self, barcode_data: str) -> Dict:
        """Check out user using barcode"""
        try:
            data = {'barcode': barcode_data}
            
            response = requests.post(
                f"{self.api_url}/api/checkout",
                json=data,
                timeout=5
            )
            
            return {
                'success': response.status_code == 200,
                'data': response.json(),
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    def draw_barcode_overlay(self, frame: np.ndarray, barcodes: List[Dict]) -> np.ndarray:
        """Draw overlay for detected barcodes"""
        for barcode in barcodes:
            # Draw rectangle around barcode
            (x, y, w, h) = barcode['rect']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw barcode data
            text = f"{barcode['type']}: {barcode['data']}"
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Draw polygon outline
            if len(barcode['polygon']) > 0:
                points = [(point.x, point.y) for point in barcode['polygon']]
                points = np.array(points, dtype=np.int32)
                cv2.polylines(frame, [points], True, (255, 0, 0), 2)
        
        return frame
    
    def start_scanning_session(self, mode='checkin', seat_id=None):
        """Start interactive barcode scanning session"""
        print(f"Starting barcode scanning session - Mode: {mode}")
        if mode == 'checkin' and seat_id:
            print(f"Target seat: {seat_id}")
        
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print("Error: Could not open camera for barcode scanning")
            return
        
        self.is_scanning = True
        
        try:
            while self.is_scanning:
                ret, frame = cap.read()
                if not ret:
                    print("Error reading frame")
                    break
                
                # Detect barcodes
                barcodes = self.decode_barcode(frame)
                
                # Process detected barcodes
                for barcode in barcodes:
                    current_time = time.time()
                    barcode_data = barcode['data']
                    
                    # Check cooldown to prevent multiple scans of same barcode
                    if (barcode_data == self.last_scanned_code and 
                        current_time - self.last_scan_time < self.scan_cooldown):
                        continue
                    
                    print(f"Barcode detected: {barcode_data}")
                    
                    # Validate barcode
                    user = self.validate_barcode(barcode_data)
                    if user:
                        print(f"Valid user: {user['name']} ({user['student_id']})")
                        
                        if mode == 'checkin':
                            if seat_id:
                                result = self.check_in_user(barcode_data, seat_id)
                                if result['success']:
                                    print(f"✅ Check-in successful: {result['data']['seat_number']}")
                                    self.last_scanned_code = barcode_data
                                    self.last_scan_time = current_time
                                else:
                                    print(f"❌ Check-in failed: {result['data'].get('error', 'Unknown error')}")
                            else:
                                print("❌ No seat specified for check-in")
                        
                        elif mode == 'checkout':
                            result = self.check_out_user(barcode_data)
                            if result['success']:
                                print(f"✅ Check-out successful: {result['data']['seat_number']}")
                                print(f"   Duration: {result['data']['duration_minutes']} minutes")
                                self.last_scanned_code = barcode_data
                                self.last_scan_time = current_time
                            else:
                                print(f"❌ Check-out failed: {result['data'].get('error', 'Unknown error')}")
                    else:
                        print(f"❌ Invalid barcode: {barcode_data}")
                
                # Draw overlay
                frame_with_overlay = self.draw_barcode_overlay(frame, barcodes)
                
                # Add instructions
                cv2.putText(frame_with_overlay, f"Mode: {mode.upper()}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                if mode == 'checkin' and seat_id:
                    cv2.putText(frame_with_overlay, f"Seat ID: {seat_id}", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                cv2.putText(frame_with_overlay, "Press 'q' to quit", (10, frame.shape[0] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Display frame
                cv2.imshow('SudarshanView - Barcode Scanner', frame_with_overlay)
                
                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
        
        except KeyboardInterrupt:
            print("Scanning stopped by user")
        
        finally:
            self.is_scanning = False
            cap.release()
            cv2.destroyAllWindows()
            print("Barcode scanning session ended")
    
    def scan_single_barcode(self, timeout=30) -> Optional[str]:
        """Scan a single barcode and return the data"""
        print("Scanning for barcode... Point camera at barcode")
        
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print("Error: Could not open camera")
            return None
        
        start_time = time.time()
        detected_barcode = None
        
        try:
            while time.time() - start_time < timeout:
                ret, frame = cap.read()
                if not ret:
                    continue
                
                barcodes = self.decode_barcode(frame)
                
                if barcodes:
                    detected_barcode = barcodes[0]['data']
                    print(f"Barcode detected: {detected_barcode}")
                    break
                
                # Display frame
                cv2.putText(frame, "Scan barcode (Press 'q' to cancel)", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.imshow('Barcode Scanner', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            pass
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        if not detected_barcode and time.time() - start_time >= timeout:
            print("Scan timeout")
        
        return detected_barcode

class BarcodeKiosk:
    """Self-service barcode scanning kiosk"""
    
    def __init__(self, api_url='http://localhost:5000'):
        self.scanner = BarcodeScanner(api_url)
        self.running = False
    
    def show_available_seats(self, hall_id=1) -> List[Dict]:
        """Get and display available seats"""
        try:
            response = requests.get(f"{self.scanner.api_url}/api/halls/{hall_id}/seats")
            if response.status_code == 200:
                seats = response.json()
                available_seats = [seat for seat in seats if not seat['is_occupied']]
                return available_seats
            return []
        except:
            return []
    
    def display_menu(self):
        """Display main menu"""
        print("\n" + "="*50)
        print("  🪑 SudarshanView - Reading Hall Kiosk")
        print("="*50)
        print("1. Check In")
        print("2. Check Out") 
        print("3. View Available Seats")
        print("4. Exit")
        print("-"*50)
    
    def run_kiosk(self):
        """Run interactive kiosk"""
        self.running = True
        print("Starting SudarshanView Kiosk...")
        
        while self.running:
            self.display_menu()
            choice = input("Select option (1-4): ").strip()
            
            if choice == '1':
                # Check In
                available_seats = self.show_available_seats()
                if not available_seats:
                    print("❌ No seats available")
                    continue
                
                print(f"\n📍 Available Seats ({len(available_seats)}):")
                for i, seat in enumerate(available_seats[:10]):  # Show first 10
                    print(f"  {i+1}. {seat['seat_number']}")
                
                try:
                    seat_choice = int(input("Select seat number (1-{}): ".format(min(10, len(available_seats))))) - 1
                    if 0 <= seat_choice < len(available_seats):
                        selected_seat = available_seats[seat_choice]
                        print(f"Selected seat: {selected_seat['seat_number']}")
                        print("Scan your ID card barcode...")
                        
                        barcode = self.scanner.scan_single_barcode(timeout=15)
                        if barcode:
                            result = self.scanner.check_in_user(barcode, selected_seat['id'])
                            if result['success']:
                                print(f"✅ Check-in successful!")
                                print(f"   Seat: {result['data']['seat_number']}")
                            else:
                                print(f"❌ Check-in failed: {result['data'].get('error', 'Unknown error')}")
                    else:
                        print("❌ Invalid seat selection")
                except ValueError:
                    print("❌ Invalid input")
            
            elif choice == '2':
                # Check Out
                print("Scan your ID card barcode to check out...")
                barcode = self.scanner.scan_single_barcode(timeout=15)
                if barcode:
                    result = self.scanner.check_out_user(barcode)
                    if result['success']:
                        print(f"✅ Check-out successful!")
                        print(f"   Seat: {result['data']['seat_number']}")
                        print(f"   Duration: {result['data']['duration_minutes']} minutes")
                    else:
                        print(f"❌ Check-out failed: {result['data'].get('error', 'Unknown error')}")
            
            elif choice == '3':
                # View Available Seats
                available_seats = self.show_available_seats()
                print(f"\n📍 Available Seats: {len(available_seats)}")
                for seat in available_seats:
                    print(f"  - {seat['seat_number']}")
            
            elif choice == '4':
                # Exit
                self.running = False
                print("👋 Thank you for using SudarshanView!")
            
            else:
                print("❌ Invalid option")
            
            if self.running:
                input("\nPress Enter to continue...")

def main():
    """Main function for testing"""
    print("SudarshanView Barcode Scanner")
    print("===========================")
    
    # Test mode selection
    print("Select mode:")
    print("1. Check-in Scanner")
    print("2. Check-out Scanner") 
    print("3. Interactive Kiosk")
    print("4. Single Barcode Scan Test")
    
    choice = input("Enter choice (1-4): ").strip()
    
    scanner = BarcodeScanner()
    
    if choice == '1':
        seat_id = input("Enter seat ID for check-in: ").strip()
        try:
            seat_id = int(seat_id)
            scanner.start_scanning_session(mode='checkin', seat_id=seat_id)
        except ValueError:
            print("Invalid seat ID")
    
    elif choice == '2':
        scanner.start_scanning_session(mode='checkout')
    
    elif choice == '3':
        kiosk = BarcodeKiosk()
        kiosk.run_kiosk()
    
    elif choice == '4':
        barcode = scanner.scan_single_barcode()
        if barcode:
            print(f"Scanned: {barcode}")
            user = scanner.validate_barcode(barcode)
            if user:
                print(f"Valid user: {user['name']}")
            else:
                print("Invalid barcode")

if __name__ == '__main__':
    main()
