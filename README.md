# Reading-hall-management

# 📚 Reading Hall Vacancy Detection System

A real-time seat occupancy monitoring system for university reading halls — providing students and administrators with up-to-date seat availability using check-in/check-out data.

---

## 🚀 Project Overview

This project aims to solve the issue of inefficient seat tracking in university reading halls. Students often waste valuable time looking for available seats, especially during peak hours. Manual monitoring is outdated, error-prone, and labor-intensive.

We propose a **software-driven seat management system** that records and displays seat usage in real time, using **barcode-based** or **manual** check-in/check-out inputs. The system avoids expensive hardware like cameras or sensors while still offering precise monitoring and analytics.

---

## 🎯 Key Features

- ✅ Student check-in/out using barcode or manual input
- 📊 Real-time seat availability display
- 🕒 Auto check-out after time limits to prevent ghost occupancy
- 🧑‍💼 Admin dashboard for monitoring and analytics
- 💡 Minimal hardware dependency

---

## 🛠️ Tech Stack

- **Frontend:** React.js
- **Backend:** Flask (Python)
- **Database:** SQLite / PostgreSQL
- **Barcode Integration:** Uses existing student ID barcodes
- **Deployment:** University server or cloud platform

---

## 🧠 System Architecture

1. Student scans barcode (or manually checks in)
2. Entry logged in database with timestamp and seat info
3. Check-out triggers duration calculation
4. Admin/user view seat map & usage logs
5. Auto check-out based on timeout rules

---

## 📊 Admin Features

- View live seat occupancy map
- Identify and reset ghost seats
- Analytics on seat usage trends
- Manual seat status override

---

## 📦 Requirements

- Python 3.x
- Flask
- React.js
- SQLite or PostgreSQL
- Barcode scanner (or mobile device with scanning support)

---

## 🧪 Installation (Coming Soon)

Setup instructions and environment details will be added after the first release.

---

## 🔮 Future Enhancements

- 📱 Mobile app for students
- 🧠 Computer vision-based optional seat tracking
- 📢 Real-time availability alerts
- 🔐 University SSO integration

---

## 📄 License

MIT License

---

## 👨‍💻 Contributors

Developed by Sarang Rao and team as part of a campus improvement initiative.
