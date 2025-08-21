#!/usr/bin/env python3
"""
Database initialization script for SudarshanView Seat Management System
Creates all required tables and initial data
"""

import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'sudarshanview.db')

def create_database():
    """Create database and all required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Users table - for students and staff
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(15),
            barcode_data VARCHAR(100) UNIQUE,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Reading halls table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reading_halls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            location VARCHAR(200),
            total_seats INTEGER NOT NULL,
            camera_url VARCHAR(500),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Seats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hall_id INTEGER NOT NULL,
            seat_number VARCHAR(10) NOT NULL,
            position_x INTEGER,
            position_y INTEGER,
            is_occupied BOOLEAN DEFAULT 0,
            is_available BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hall_id) REFERENCES reading_halls (id),
            UNIQUE(hall_id, seat_number)
        )
    ''')
    
    # Sessions table - tracks check-in/check-out
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            seat_id INTEGER NOT NULL,
            hall_id INTEGER NOT NULL,
            check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            check_out_time TIMESTAMP,
            check_in_method VARCHAR(20) DEFAULT 'barcode', -- 'barcode' or 'vision'
            check_out_method VARCHAR(20), -- 'barcode', 'vision', 'timeout'
            duration_minutes INTEGER,
            is_active BOOLEAN DEFAULT 1,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (seat_id) REFERENCES seats (id),
            FOREIGN KEY (hall_id) REFERENCES reading_halls (id)
        )
    ''')
    
    # Vision detections table - for computer vision logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vision_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seat_id INTEGER NOT NULL,
            is_occupied BOOLEAN NOT NULL,
            confidence REAL DEFAULT 0.0,
            detection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_path VARCHAR(500),
            FOREIGN KEY (seat_id) REFERENCES seats (id)
        )
    ''')
    
    # System configurations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key VARCHAR(50) UNIQUE NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Activity logs for audit trail
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action VARCHAR(100) NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(45),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert initial configurations
    configs = [
        ('idle_timeout_minutes', '30', 'Minutes before auto-checkout for idle seats'),
        ('vision_confidence_threshold', '0.7', 'Minimum confidence for vision detection'),
        ('auto_checkout_enabled', 'true', 'Enable automatic checkout based on vision'),
        ('max_session_hours', '8', 'Maximum hours for a single session'),
        ('notification_enabled', 'true', 'Enable system notifications')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO configurations (key, value, description)
        VALUES (?, ?, ?)
    ''', configs)
    
    # Insert sample reading hall
    cursor.execute('''
        INSERT OR IGNORE INTO reading_halls (name, location, total_seats, camera_url)
        VALUES ('Main Reading Hall', 'Ground Floor, Library Building', 50, 'http://localhost:8080/video_feed')
    ''')
    
    # Get the hall ID for seat creation
    cursor.execute('SELECT id FROM reading_halls WHERE name = "Main Reading Hall"')
    hall_id = cursor.fetchone()[0]
    
    # Insert sample seats
    seats_data = []
    for row in range(1, 6):  # 5 rows
        for col in range(1, 11):  # 10 columns each
            seat_number = f"R{row}S{col}"
            # Calculate approximate positions (assuming 800x600 camera resolution)
            pos_x = 50 + (col * 70)
            pos_y = 50 + (row * 100)
            seats_data.append((hall_id, seat_number, pos_x, pos_y))
    
    cursor.executemany('''
        INSERT OR IGNORE INTO seats (hall_id, seat_number, position_x, position_y)
        VALUES (?, ?, ?, ?)
    ''', seats_data)
    
    # Insert sample users
    sample_users = [
        ('STU001', 'John Doe', 'john.doe@university.edu', '9876543210', 'BARCODE001'),
        ('STU002', 'Jane Smith', 'jane.smith@university.edu', '9876543211', 'BARCODE002'),
        ('STU003', 'Mike Johnson', 'mike.johnson@university.edu', '9876543212', 'BARCODE003')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO users (student_id, name, email, phone, barcode_data)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_users)
    
    conn.commit()
    conn.close()
    
    print(f"Database created successfully at: {DATABASE_PATH}")
    print("Sample data inserted:")
    print("- 1 Reading Hall (50 seats)")
    print("- 50 Seats arranged in 5 rows x 10 columns")
    print("- 3 Sample users")
    print("- System configurations")

def reset_database():
    """Reset database by dropping all tables and recreating"""
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print("Existing database removed.")
    create_database()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_database()
    else:
        create_database()
