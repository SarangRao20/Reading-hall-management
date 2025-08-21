# SudarshanView: Real-Time Reading Hall Seat Management System

A comprehensive seat management solution combining computer vision and minimal check-in systems for efficient reading hall monitoring.

## 🎯 Project Overview

SudarshanView addresses the inefficiencies in college reading hall seat management by leveraging:
- **Computer Vision (OpenCV)** for passive seat occupancy detection
- **ID Card Barcode System** for check-in/check-out verification
- **Real-time Dashboard** for administrators
- **Automated Session Management** with idle timeout detection

## 🏗️ System Architecture

```
├── backend/           # Flask API server
├── frontend/          # React admin dashboard
├── computer_vision/   # OpenCV seat detection
├── database/         # Database schemas and migrations
├── config/          # Configuration files
└── docs/           # Documentation
```

## 🚀 Features

- **Real-time Seat Monitoring**: Live occupancy detection via CCTV feeds
- **Hybrid Check-in System**: Barcode scanning with vision-based verification
- **Automated Checkout**: Time-based idle detection and seat release
- **Admin Dashboard**: Live monitoring, analytics, and session logs
- **Scalable Architecture**: Easy deployment across multiple halls

## 🛠️ Technology Stack

- **Backend**: Python, Flask, PostgreSQL/SQLite
- **Frontend**: React, JavaScript
- **Computer Vision**: OpenCV, Python
- **Database**: PostgreSQL (production), SQLite (development)
- **Deployment**: Docker, Cloud/University servers

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL (for production)
- CCTV camera access
- Barcode scanners

## 🚀 Quick Start

1. **Clone and Setup**:
   ```bash
   cd SudarshanView-Seat-Management
   pip install -r requirements.txt
   npm install --prefix frontend
   ```

2. **Configure Environment**:
   ```bash
   cp config/.env.example .env
   # Edit .env with your database and camera settings
   ```

3. **Initialize Database**:
   ```bash
   python database/init_db.py
   ```

4. **Start Services**:
   ```bash
   # Backend
   python backend/app.py
   
   # Frontend
   cd frontend && npm start
   
   # Computer Vision Service
   python computer_vision/main.py
   ```

## 📊 Expected Outcomes

- ✅ Automatic inactive seat detection and release
- ✅ Real-time admin dashboard for seat monitoring
- ✅ Comprehensive session logging and analytics
- ✅ Improved seat utilization during peak hours
- ✅ Scalable deployment model for multiple halls

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:
- [API Documentation](docs/api.md)
- [Computer Vision Setup](docs/vision_setup.md)
- [Deployment Guide](docs/deployment.md)

## 🤝 Contributing

Please read our [Contributing Guidelines](docs/CONTRIBUTING.md) before submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

Developed as part of the CEP (Capstone Engineering Project) initiative.
