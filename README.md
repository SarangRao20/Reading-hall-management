# Seat Occupancy Detector

FastAPI app using Ultralytics YOLO + MediaPipe to detect seats and occupancy from video.

## Features
- YOLO-based chair/person detection
- Calibration to map detected chairs to a grid
- WebSocket-ready for real-time dashboard
- Exportable occupancy logs (extendable)

## Quickstart (Windows)
1. Create and activate venv:
   ```powershell
   py -3 -m venv myenv
   .\myenv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   python -m pip install -U pip
   # Install exact, pinned versions for reproducible environments
   python -m pip install -r requirements.txt
   ```
   Note: install a Torch build compatible with your CUDA if needed (see https://pytorch.org).

3. Configure (optional)
   - Edit `app.py` constants (VIDEO_PATH, MODEL_PATH, thresholds) or use environment variables.

4. Run:
   ```powershell
   python -m uvicorn app:app --host 0.0.0.0 --port 8000
   ```
   Open: http://127.0.0.1:8000/

## Development suggestions
- Add a WebSocket front-end dashboard showing live seat map and heatmap.
- Export occupancy history endpoints (CSV/JSON).
- Add unit tests for calibration/clustering; CI via GitHub Actions.
- Provide a Dockerfile / docker-compose for deployment.

## Notes
- If you hit import errors in VS Code, select the project interpreter (myenv) and install deps into it.
- Use `opencv-python` instead of `opencv-python-headless` for local GUI debugging.
 - `requirements.txt` contains exact, pinned versions captured from the development venv.
 - To create a development environment with flexible updates, consider adding `requirements-dev.txt`.
- Adjust YOLO confidence thresholds in `app.py` for better detection based on your video quality.