# SudarshanView Setup Guide

This guide will help you set up and run the SudarshanView seat management system.

## 📋 Prerequisites

### Software Requirements
- Python 3.8 or higher
- Node.js 16 or higher
- Git (for version control)
- Camera/CCTV access for computer vision
- Barcode scanner or camera for ID card scanning

### Hardware Requirements
- Computer with webcam or connected CCTV system
- Barcode scanner (or secondary camera)
- Sufficient processing power for OpenCV operations

## 🚀 Quick Start

### 1. Clone or Navigate to Project Directory
```bash
cd SudarshanView-Seat-Management
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Initialize the database
python database/init_db.py

# Start the Flask backend
python backend/app.py
```
The backend will be available at `http://localhost:5000`

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the React development server
npm start
```
The frontend will be available at `http://localhost:3000`

### 4. Computer Vision System
```bash
# Run the computer vision detection system
python computer_vision/main.py
```

### 5. Barcode Scanner (Optional)
```bash
# Test the barcode scanner
python backend/utils/barcode_scanner.py
```

## 🔧 Configuration

### Environment Setup
1. Copy the environment template:
```bash
cp config/.env.example .env
```

2. Edit `.env` file with your specific settings:
- Camera URLs/IDs
- Database configuration
- API endpoints
- Detection parameters

### Computer Vision Configuration
Edit `config/vision_config.json` to adjust:
- Detection intervals
- Confidence thresholds
- Camera settings
- YOLO configuration (if using)

## 📊 System Components

### 1. Database
- SQLite database is created automatically
- Contains tables for users, seats, sessions, analytics
- Sample data is inserted during initialization

### 2. Backend API
- Flask REST API server
- Handles user management, seat tracking, analytics
- Auto-cleanup of expired sessions
- Integration endpoints for computer vision

### 3. Frontend Dashboard
- React-based admin interface
- Real-time seat monitoring
- Analytics and reporting
- User and session management

### 4. Computer Vision
- OpenCV-based seat detection
- Supports basic motion detection and YOLO
- Automatic checkout for idle seats
- Detection logging and image saving

### 5. Barcode Integration
- ID card scanning for check-in/out
- Interactive kiosk mode
- Fallback verification system

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build
```bash
# Build the image
docker build -t sudarshanview .

# Run the container
docker run -p 5000:5000 -v $(pwd)/database:/app/database sudarshanview
```

## 📱 Usage Guide

### Admin Dashboard
1. Open `http://localhost:3000` in your browser
2. Navigate through different sections:
   - **Dashboard**: Overview and real-time statistics
   - **Seat Layout**: Visual seat map with live status
   - **Analytics**: Usage reports and trends
   - **Users**: Student/staff management
   - **Sessions**: Session history and management
   - **Settings**: System configuration

### Student Check-in/Check-out
1. **Using Barcode Scanner**:
   - Run the barcode kiosk: `python backend/utils/barcode_scanner.py`
   - Select check-in mode
   - Choose available seat
   - Scan student ID barcode

2. **Using API Directly**:
   ```bash
   # Check-in
   curl -X POST http://localhost:5000/api/checkin \
     -H "Content-Type: application/json" \
     -d '{"barcode": "BARCODE001", "seat_id": 1}'
   
   # Check-out
   curl -X POST http://localhost:5000/api/checkout \
     -H "Content-Type: application/json" \
     -d '{"barcode": "BARCODE001"}'
   ```

### Computer Vision Monitoring
1. Start the vision system: `python computer_vision/main.py`
2. System will:
   - Monitor seat occupancy via camera feed
   - Automatically detect empty seats
   - Checkout users after idle timeout
   - Log all detections for analysis

## 🔍 API Endpoints

### Analytics
- `GET /api/analytics/overview` - System overview stats
- `GET /api/analytics/usage?days=7` - Usage analytics

### User Management
- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `GET /api/users/{barcode}` - Get user by barcode

### Seat Management
- `GET /api/halls` - List reading halls
- `GET /api/halls/{id}/seats` - Get seats in hall

### Session Management
- `POST /api/checkin` - Check-in user
- `POST /api/checkout` - Check-out user
- `GET /api/sessions/active` - List active sessions

### Computer Vision
- `POST /api/vision/detection` - Submit vision detection

## 🛠️ Troubleshooting

### Common Issues

1. **Camera not detected**
   - Check camera permissions
   - Verify camera ID in config
   - Ensure no other applications are using the camera

2. **Database errors**
   - Run `python database/init_db.py --reset` to recreate database
   - Check file permissions in database directory

3. **Frontend not connecting to backend**
   - Verify backend is running on port 5000
   - Check CORS settings in Flask app
   - Ensure proxy setting in package.json

4. **Barcode scanner not working**
   - Install required dependencies: `pip install pyzbar`
   - Check camera permissions
   - Ensure adequate lighting for barcode scanning

5. **Computer vision detection issues**
   - Adjust confidence thresholds in config
   - Improve lighting conditions
   - Calibrate seat positions in database

### Log Files
- Backend logs: Check console output or configure logging
- Vision system: Detection logs and saved images in `detections/`
- Database: SQL operations logged to console

### Performance Optimization
1. **Reduce detection frequency** - Increase `detection_interval` in config
2. **Optimize camera resolution** - Lower resolution for better performance
3. **Use YOLO for better accuracy** - Download YOLO weights and enable in config
4. **Database optimization** - Use PostgreSQL for production

## 📈 Monitoring and Analytics

### Available Metrics
- Real-time occupancy rates
- Daily/weekly usage trends
- Average session duration
- Peak usage hours
- User activity patterns

### Accessing Data
- Web dashboard at `http://localhost:3000`
- REST API endpoints for integration
- Direct database queries (SQLite browser)
- Exported CSV reports (future feature)

## 🔒 Security Considerations

### Current Implementation
- Basic barcode validation
- Session management
- Input sanitization in APIs

### Production Recommendations
- Enable HTTPS/SSL
- Add user authentication
- Implement rate limiting
- Regular database backups
- Camera feed encryption
- Secure barcode generation

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

### Code Structure
```
├── backend/          # Flask API server
├── frontend/         # React dashboard
├── computer_vision/  # OpenCV detection
├── database/        # SQLite database
├── config/          # Configuration files
└── docs/           # Documentation
```

## 📞 Support

For issues and questions:
- Check troubleshooting section
- Review error logs
- Create GitHub issue with details
- Contact project maintainers

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

**SudarshanView** - Making reading hall management efficient through computer vision and minimal user interaction.
