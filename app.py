import os
import cv2
import threading
import asyncio
import json
import re
import math
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO
import mediapipe as mp

# Initialize FastAPI
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global state
seat_status = {}
lock = threading.Lock()
calibration_data = []
fixed_chair_boxes = []
is_calibrated = False

# Load Models
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
model = YOLO("yolov8m.pt")
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

# Video source
VIDEO_PATH = "vedio3.mp4"

# 6x5 Grid Layout (Rows x Columns)
# Derived from SVG analysis
GRID_LAYOUT = [
    ["seat-01", "seat-06", "seat-05", "seat-02", "seat-04", "seat-03"], # Row 0
    ["seat-19", "seat-24", "seat-23", "seat-20", "seat-22", "seat-21"], # Row 1
    ["seat-07", "seat-12", "seat-11", "seat-08", "seat-10", "seat-09"], # Row 2
    ["seat-13", "seat-18", "seat-17", "seat-14", "seat-16", "seat-15"], # Row 3
    ["seat-25", "seat-30", "seat-29", "seat-26", "seat-28", "seat-27"]  # Row 4
]
ALL_SEAT_IDS = [seat for row in GRID_LAYOUT for seat in row]

def process_video():
    global seat_status, is_calibrated, fixed_chair_boxes
    cap = cv2.VideoCapture(VIDEO_PATH)
    frame_count = 0
    CALIBRATION_FRAMES = 45
    
    print("Starting video processing...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        frame = cv2.resize(frame, (960, 540))
        
        # YOLO Detection
        results = model(frame, verbose=False, conf=0.4)[0]
        chairs = []
        persons = []
        
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])
            if conf < 0.4:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if label == "chair":
                chairs.append((x1, y1, x2, y2))
            elif label == "person":
                persons.append((x1, y1, x2, y2))
        
        # Calibration Phase
        if not is_calibrated:
            frame_count += 1
            print(f"Calibrating... Frame {frame_count}/{CALIBRATION_FRAMES}")
            calibration_data.extend(chairs)
            
            if frame_count >= CALIBRATION_FRAMES:
                print("Calibration complete. Computing grid mapping...")
                
                # 1. Cluster detections to find unique chairs
                clusters = []
                THRESHOLD = 50 
                
                for box in calibration_data:
                    cx = (box[0] + box[2]) / 2
                    cy = (box[1] + box[3]) / 2
                    matched = False
                    for cluster in clusters:
                        ccx = sum(c['cx'] for c in cluster['points']) / len(cluster['points'])
                        ccy = sum(c['cy'] for c in cluster['points']) / len(cluster['points'])
                        dist = ((cx - ccx)**2 + (cy - ccy)**2)**0.5
                        if dist < THRESHOLD:
                            cluster['points'].append({'cx': cx, 'cy': cy, 'box': box})
                            matched = True
                            break
                    if not matched:
                        clusters.append({'points': [{'cx': cx, 'cy': cy, 'box': box}]})
                
                # 2. Compute stable centroids
                stable_chairs = []
                for cluster in clusters:
                    if len(cluster['points']) < (CALIBRATION_FRAMES * 0.4):
                        continue
                    avg_x1 = sum(p['box'][0] for p in cluster['points']) / len(cluster['points'])
                    avg_y1 = sum(p['box'][1] for p in cluster['points']) / len(cluster['points'])
                    avg_x2 = sum(p['box'][2] for p in cluster['points']) / len(cluster['points'])
                    avg_y2 = sum(p['box'][3] for p in cluster['points']) / len(cluster['points'])
                    
                    cx = (avg_x1 + avg_x2) / 2
                    cy = (avg_y1 + avg_y2) / 2
                    
                    stable_chairs.append({
                        'box': (int(avg_x1), int(avg_y1), int(avg_x2), int(avg_y2)),
                        'cx': cx,
                        'cy': cy,
                        'occupied': False,
                        'id': None
                    })
                
                if not stable_chairs:
                    print("No stable chairs found!")
                    is_calibrated = True
                    continue

                # 3. Grid Snapping
                # Find bounding box of all centroids
                min_x = min(c['cx'] for c in stable_chairs)
                max_x = max(c['cx'] for c in stable_chairs)
                min_y = min(c['cy'] for c in stable_chairs)
                max_y = max(c['cy'] for c in stable_chairs)
                
                # Avoid division by zero
                if max_x == min_x: max_x += 1
                if max_y == min_y: max_y += 1
                
                # Steps for 6 columns (5 intervals) and 5 rows (4 intervals)
                step_x = (max_x - min_x) / 5
                step_y = (max_y - min_y) / 4
                
                print(f"Grid Bounds: X[{min_x:.1f}, {max_x:.1f}], Y[{min_y:.1f}, {max_y:.1f}]")
                print(f"Step Sizes: X={step_x:.1f}, Y={step_y:.1f}")
                
                fixed_chair_boxes = []
                for chair in stable_chairs:
                    # Calculate logical index
                    col_idx = int(round((chair['cx'] - min_x) / step_x))
                    row_idx = int(round((chair['cy'] - min_y) / step_y))
                    
                    # Clamp to grid limits
                    col_idx = max(0, min(col_idx, 5))
                    row_idx = max(0, min(row_idx, 4))
                    
                    # Assign ID
                    chair['id'] = GRID_LAYOUT[row_idx][col_idx]
                    chair['grid_pos'] = (row_idx, col_idx)
                    fixed_chair_boxes.append(chair)
                    print(f"Mapped Chair at ({chair['cx']:.0f}, {chair['cy']:.0f}) -> Grid({row_idx}, {col_idx}) -> {chair['id']}")
                
                print(f"Mapped {len(fixed_chair_boxes)} chairs to grid.")
                is_calibrated = True
            
            with lock:
                seat_status = {"status": "calibrating", "progress": f"{frame_count}/{CALIBRATION_FRAMES}"}
            cv2.waitKey(30)
            continue

        # Normal Operation
        
        # Pose Estimation
        person_statuses = []
        for (x1, y1, x2, y2) in persons:
            person_crop = frame[y1:y2, x1:x2]
            if person_crop.size == 0:
                person_statuses.append("Standing")
                continue
            person_rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
            mp_results = pose.process(person_rgb)
            status = "Standing"
            if mp_results.pose_landmarks:
                landmarks = mp_results.pose_landmarks.landmark
                left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP].y
                right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y
                left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y
                right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
                hip_y = (left_hip + right_hip) / 2
                shoulder_y = (left_shoulder + right_shoulder) / 2
                ratio = (hip_y - shoulder_y)
                if ratio >= 0.15:
                    status = "Sitting"
            person_statuses.append(status)

        # Check Occupancy
        for chair in fixed_chair_boxes:
            chair['occupied'] = False
            cx1, cy1, cx2, cy2 = chair['box']
            
            # Debug: Draw chair box and ID
            cv2.rectangle(frame, (cx1, cy1), (cx2, cy2), (255, 0, 0), 2)
            cv2.putText(frame, str(chair['id']), (cx1, cy1 - 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

            for p_idx, person_box in enumerate(persons):
                if person_statuses[p_idx] == "Sitting":
                    px1, py1, px2, py2 = person_box
                    ix1 = max(cx1, px1)
                    iy1 = max(cy1, py1)
                    ix2 = min(cx2, px2)
                    iy2 = min(cy2, py2)
                    if ix2 > ix1 and iy2 > iy1:
                        intersection_area = (ix2 - ix1) * (iy2 - iy1)
                        chair_area = (cx2 - cx1) * (cy2 - cy1)
                        if intersection_area > 0.3 * chair_area:
                            chair['occupied'] = True
                            # Debug: Draw occupied status
                            cv2.rectangle(frame, (cx1, cy1), (cx2, cy2), (0, 255, 0), 2)
                            break
        
        # Update Global State
        new_status = {}
        # Initialize all as vacant
        for seat_id in ALL_SEAT_IDS:
            new_status[seat_id] = "vacant"
            
        # Update occupied ones
        for chair in fixed_chair_boxes:
            if chair['id'] and chair['occupied']:
                new_status[chair['id']] = "occupied"

        with lock:
            seat_status = new_status
            
        cv2.imshow("Debug View", frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

# Start background thread
thread = threading.Thread(target=process_video, daemon=True)
thread.start()

@app.get("/")
async def get():
    with open("index.html", "r") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            with lock:
                current_status = seat_status.copy()
            
            total = len(ALL_SEAT_IDS)
            occupied = sum(1 for v in current_status.values() if v == "occupied")
            vacant = total - occupied
            
            data = {
                "seats": current_status,
                "stats": {
                    "total": total,
                    "occupied": occupied,
                    "vacant": vacant
                }
            }
            
            await websocket.send_json(data)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
