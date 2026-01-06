import os
import cv2
from ultralytics import YOLO
import mediapipe as mp

# Suppress TensorFlow logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Load YOLOv8 model
model = YOLO("yolov8m.pt")

# Initialize Mediapipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

# Video source
video_path = "vedio3.mp4"
cap = cv2.VideoCapture(video_path)

# Ground truth values
GT_CHAIRS = 23
GT_SITTING = 12

frame_count = 0
paused = False  # For pause/play toggle

while True:
    if not paused:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

    frame = cv2.resize(frame, (960, 540))

    # Run YOLO only when not paused (avoid recomputation)
    if not paused:
        results = model(frame, verbose=False, conf=0.4)[0]
        chairs, persons = [], []

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

        sitting_count, standing_count = 0, 0
        statuses = []
        for (x1, y1, x2, y2) in persons:
            person_crop = frame[y1:y2, x1:x2]
            if person_crop.size == 0:
                statuses.append("Standing")
                standing_count += 1
                continue

            person_rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
            mp_results = pose.process(person_rgb)

            if mp_results.pose_landmarks:
                landmarks = mp_results.pose_landmarks.landmark
                left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP].y
                right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y
                left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y
                right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
                hip_y = (left_hip + right_hip) / 2
                shoulder_y = (left_shoulder + right_shoulder) / 2
                ratio = (hip_y - shoulder_y)
                status = "Standing" if ratio < 0.15 else "Sitting"
            else:
                status = "Standing"

            statuses.append(status)
            if status == "Sitting":
                sitting_count += 1
            else:
                standing_count += 1

    # Draw detections
    for (cx1, cy1, cx2, cy2) in chairs:
        cv2.rectangle(frame, (cx1, cy1), (cx2, cy2), (255, 0, 0), 2)
    for (pbox, status) in zip(persons, statuses):
        x1, y1, x2, y2 = pbox
        color = (0, 255, 0) if status == "Sitting" else (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, status, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Calculate accuracies
    chair_acc = (min(len(chairs), GT_CHAIRS) / GT_CHAIRS) * 100 if GT_CHAIRS else 0
    sitting_acc = (min(sitting_count, GT_SITTING) / GT_SITTING) * 100 if GT_SITTING else 0

    # Dashboard
    cv2.rectangle(frame, (10, 10), (330, 120), (0, 0, 0), -1)
    cv2.putText(frame, f"Sitting (Green): {sitting_count}", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f"Standing (Red): {standing_count}", (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.putText(frame, f"Chairs (Blue): {len(chairs)}", (20, 85),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    cv2.putText(frame, f"Sitting Acc: {sitting_acc:.1f}%", (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    # Frame counter & pause info
    cv2.putText(frame, f"Frame: {frame_count}", (820, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    if paused:
        cv2.putText(frame, "PAUSED", (820, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Show frame
    cv2.imshow("YOLO + Mediapipe Visualization", frame)

    # Keyboard controls
    key = cv2.waitKey(20) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):  # spacebar to pause/play
        paused = not paused

cap.release()
cv2.destroyAllWindows()
