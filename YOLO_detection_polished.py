import cv2
from collections import deque
from ultralytics import YOLO

# =======================
# TUNABLE PARAMETERS
# =======================
WEBCAM_INDEX       = 1              # IRIS webcam
MODEL_PATH         = "yolov8n.pt"   # use yolov8s.pt for better accuracy
CONF_CHAIR         = 0.35
CONF_PERSON        = 0.35
INIT_FRAMES        = 20             # initial frames to detect seats
INIT_STRIDE        = 1
IOU_DUPE_THRESH    = 0.5
SEAT_EXPAND_SCALE  = 1.25
SMOOTH_WINDOW      = 5
PERSON_BOX_THICK   = 1
SEAT_DOT_RADIUS    = 6
SHOW_PERSON_BOXES  = True
FONT = cv2.FONT_HERSHEY_SIMPLEX

# =======================
# HELPER FUNCTIONS
# =======================
def iou(a, b):
    x1 = max(a[0], b[0]); y1 = max(a[1], b[1])
    x2 = min(a[2], b[2]); y2 = min(a[3], b[3])
    inter = max(0, x2-x1) * max(0, y2-y1)
    if inter <= 0: return 0.0
    area_a = (a[2]-a[0]) * (a[3]-a[1])
    area_b = (b[2]-b[0]) * (b[3]-b[1])
    return inter / float(area_a + area_b - inter)

def merge_unique_boxes(boxes, iou_thresh):
    uniques = []
    for b in boxes:
        if all(iou(b, u) < iou_thresh for u in uniques):
            uniques.append(b)
    return uniques

def expand_box(box, scale, w_limit, h_limit):
    x1,y1,x2,y2 = box
    w = x2-x1; h = y2-y1
    cx = x1 + w/2.0; cy = y1 + h/2.0
    nw = w * scale; nh = h * scale
    ex1 = int(max(0, cx - nw/2)); ey1 = int(max(0, cy - nh/2))
    ex2 = int(min(w_limit-1, cx + nw/2)); ey2 = int(min(h_limit-1, cy + nh/2))
    return (ex1, ey1, ex2, ey2)

def hip_point(person_box):
    x1,y1,x2,y2 = person_box
    cx = int((x1 + x2)/2)
    hy = int(y1 + 0.70*(y2 - y1))
    return (cx, hy)

def point_in_rect(pt, rect):
    x,y = pt; x1,y1,x2,y2 = rect
    return (x1 <= x <= x2) and (y1 <= y <= y2)

def draw_label_pill(img, x, y, text, bg_color, txt_color=(255,255,255)):
    pad_x = 6; pad_y = 4
    (tw, th), _ = cv2.getTextSize(text, FONT, 0.5, 1)
    bx1 = max(0, x); by1 = max(0, y - th - pad_y*2)
    bx2 = min(img.shape[1]-1, x + tw + pad_x*2)
    by2 = min(img.shape[0]-1, y)
    cv2.rectangle(img, (bx1,by1), (bx2,by2), bg_color, -1)
    cv2.putText(img, text, (bx1 + pad_x, by2 - pad_y), FONT, 0.5, txt_color, 1, cv2.LINE_AA)

# =======================
# LOAD MODEL & WEBCAM
# =======================
model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(WEBCAM_INDEX)
ok, frame = cap.read()
if not ok:
    raise RuntimeError("Could not read from IRIS webcam. Check WEBCAM_INDEX.")

H, W = frame.shape[:2]

# =======================
# PHASE 1: INITIAL SEAT MAP DETECTION
# =======================
print("[INFO] Building seat map…")
init_boxes = []
frame_idx = 0

while frame_idx < INIT_FRAMES:
    ok, frame = cap.read()
    if not ok: break
    frame_idx += 1
    if frame_idx % INIT_STRIDE != 0: continue

    results = model(frame, conf=CONF_CHAIR, verbose=False)[0]
    for b in results.boxes:
        cls = int(b.cls[0])
        if model.names[cls] != "chair": continue
        conf = float(b.conf[0])
        if conf < CONF_CHAIR: continue
        x1,y1,x2,y2 = map(int, b.xyxy[0])
        if (x2-x1)<20 or (y2-y1)<20: continue
        init_boxes.append((x1,y1,x2,y2))

seat_boxes = merge_unique_boxes(init_boxes, IOU_DUPE_THRESH)
seat_boxes = sorted(seat_boxes, key=lambda b: ((b[1]+b[3])//2, (b[0]+b[2])//2))

if len(seat_boxes) == 0:
    print("[WARN] No chairs detected; fallback to live detection.")

smooth_buffers = [deque(maxlen=SMOOTH_WINDOW) for _ in seat_boxes]
stable_status = ["Empty" for _ in seat_boxes]

print(f"[INFO] Seats detected: {len(seat_boxes)}")

# =======================
# PHASE 2: REAL-TIME DETECTION LOOP
# =======================
frame_no = 0
while True:
    ok, frame = cap.read()
    if not ok: break
    frame_no += 1

    results = model(frame, conf=min(CONF_PERSON, CONF_CHAIR), verbose=False)[0]
    persons = []
    live_chairs = []

    for b in results.boxes:
        cls = int(b.cls[0])
        name = model.names[cls]
        conf = float(b.conf[0])
        x1,y1,x2,y2 = map(int, b.xyxy[0])

        if name == "person" and conf >= CONF_PERSON:
            persons.append((x1,y1,x2,y2))
        elif name == "chair" and conf >= CONF_CHAIR and len(seat_boxes)==0:
            live_chairs.append((x1,y1,x2,y2))

    seats_current = seat_boxes if len(seat_boxes) else live_chairs
    occupied_flags = []

    for idx, sb in enumerate(seats_current):
        ex = expand_box(sb, SEAT_EXPAND_SCALE, W, H)
        occ = any(point_in_rect(hip_point(pb), ex) for pb in persons)
        occupied_flags.append(occ)

        color = (0,0,255) if occ else (0,180,0)
        cx, cy = (sb[0]+sb[2])//2, (sb[1]+sb[3])//2
        cv2.circle(frame, (cx, cy), SEAT_DOT_RADIUS, color, -1)
        draw_label_pill(frame, sb[0], max(20, sb[1]-10), f"Seat {idx+1}", color)

    # Smooth occupancy
    if len(seat_boxes) == len(occupied_flags) and len(seat_boxes) > 0:
        for i, flag in enumerate(occupied_flags):
            smooth_buffers[i].append(1 if flag else 0)
            avg = sum(smooth_buffers[i]) / len(smooth_buffers[i])
            stable_status[i] = "Occupied" if avg >= 0.6 else "Empty"

    # Top bar info
    occ_count = stable_status.count("Occupied") if seat_boxes else sum(occupied_flags)
    total_seats = len(seat_boxes) if seat_boxes else len(seats_current)
    empty_count = max(0, total_seats - occ_count)
    cv2.rectangle(frame, (0,0), (W,42), (35,35,35), -1)
    top_text = f"Frame {frame_no} | Seats: {total_seats} | Occupied: {occ_count} | Empty: {empty_count} | Persons: {len(persons)}"
    cv2.putText(frame, top_text, (12,28), FONT, 0.7, (255,255,255), 2, cv2.LINE_AA)

    # Person boxes
    if SHOW_PERSON_BOXES:
        for x1,y1,x2,y2 in persons:
            cv2.rectangle(frame, (x1,y1), (x2,y2), (255,120,0), PERSON_BOX_THICK)
            hx, hy = hip_point((x1,y1,x2,y2))
            cv2.circle(frame, (hx,hy), 3, (255,120,0), -1)

    cv2.imshow("IRIS Webcam - Seat Occupancy", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
