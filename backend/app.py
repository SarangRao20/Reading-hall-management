#!/usr/bin/env python3
"""
SudarshanView Backend API Server
Flask application providing REST APIs for seat management system
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import os
import json
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Database configuration
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'sudarshanview.db')

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_activity(user_id, action, details=None, ip_address=None):
    """Log user activity"""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO activity_logs (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)',
        (user_id, action, details, ip_address)
    )
    conn.commit()
    conn.close()

# ==================== USER MANAGEMENT APIs ====================

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users WHERE is_active = 1').fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user"""
    data = request.get_json()
    
    required_fields = ['student_id', 'name', 'barcode_data']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute(
            '''INSERT INTO users (student_id, name, email, phone, barcode_data)
               VALUES (?, ?, ?, ?, ?)''',
            (data['student_id'], data['name'], data.get('email'), 
             data.get('phone'), data['barcode_data'])
        )
        conn.commit()
        user_id = conn.lastrowid
        log_activity(user_id, 'USER_CREATED', f"New user: {data['name']}")
        conn.close()
        return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Student ID or barcode already exists'}), 409

@app.route('/api/users/<barcode>', methods=['GET'])
def get_user_by_barcode(barcode):
    """Get user by barcode"""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE barcode_data = ? AND is_active = 1', 
                       (barcode,)).fetchone()
    conn.close()
    
    if user:
        return jsonify(dict(user))
    return jsonify({'error': 'User not found'}), 404

# ==================== READING HALLS APIs ====================

@app.route('/api/halls', methods=['GET'])
def get_halls():
    """Get all reading halls"""
    conn = get_db_connection()
    halls = conn.execute('SELECT * FROM reading_halls WHERE is_active = 1').fetchall()
    conn.close()
    return jsonify([dict(hall) for hall in halls])

@app.route('/api/halls/<int:hall_id>/seats', methods=['GET'])
def get_hall_seats(hall_id):
    """Get all seats in a specific hall with current status"""
    conn = get_db_connection()
    
    # Get seats with current session info
    seats = conn.execute('''
        SELECT s.*, 
               sess.user_id as current_user_id,
               u.name as current_user_name,
               sess.check_in_time,
               sess.last_activity
        FROM seats s
        LEFT JOIN sessions sess ON s.id = sess.seat_id AND sess.is_active = 1
        LEFT JOIN users u ON sess.user_id = u.id
        WHERE s.hall_id = ? AND s.is_available = 1
        ORDER BY s.seat_number
    ''', (hall_id,)).fetchall()
    
    conn.close()
    return jsonify([dict(seat) for seat in seats])

# ==================== SESSION MANAGEMENT APIs ====================

@app.route('/api/checkin', methods=['POST'])
def check_in():
    """Check in user to a seat"""
    data = request.get_json()
    
    required_fields = ['barcode', 'seat_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    
    # Get user by barcode
    user = conn.execute('SELECT id FROM users WHERE barcode_data = ? AND is_active = 1',
                       (data['barcode'],)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'Invalid barcode'}), 404
    
    # Check if seat is available
    seat = conn.execute('SELECT * FROM seats WHERE id = ? AND is_available = 1 AND is_occupied = 0',
                       (data['seat_id'],)).fetchone()
    if not seat:
        conn.close()
        return jsonify({'error': 'Seat not available'}), 409
    
    # Check if user already has an active session
    active_session = conn.execute('SELECT id FROM sessions WHERE user_id = ? AND is_active = 1',
                                 (user['id'],)).fetchone()
    if active_session:
        conn.close()
        return jsonify({'error': 'User already has an active session'}), 409
    
    try:
        # Create new session
        conn.execute('''
            INSERT INTO sessions (user_id, seat_id, hall_id, check_in_method)
            VALUES (?, ?, ?, ?)
        ''', (user['id'], data['seat_id'], seat['hall_id'], 'barcode'))
        
        # Update seat status
        conn.execute('UPDATE seats SET is_occupied = 1 WHERE id = ?', (data['seat_id'],))
        
        session_id = conn.lastrowid
        conn.commit()
        
        log_activity(user['id'], 'CHECK_IN', f"Checked in to seat {seat['seat_number']}")
        conn.close()
        
        return jsonify({
            'message': 'Check-in successful',
            'session_id': session_id,
            'seat_number': seat['seat_number']
        }), 201
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': 'Check-in failed'}), 500

@app.route('/api/checkout', methods=['POST'])
def check_out():
    """Check out user from their current seat"""
    data = request.get_json()
    
    if 'barcode' not in data:
        return jsonify({'error': 'Missing barcode'}), 400
    
    conn = get_db_connection()
    
    # Get user and active session
    session = conn.execute('''
        SELECT sess.*, u.name, s.seat_number
        FROM sessions sess
        JOIN users u ON sess.user_id = u.id
        JOIN seats s ON sess.seat_id = s.id
        WHERE u.barcode_data = ? AND sess.is_active = 1
    ''', (data['barcode'],)).fetchone()
    
    if not session:
        conn.close()
        return jsonify({'error': 'No active session found'}), 404
    
    try:
        # Calculate duration
        check_in_time = datetime.fromisoformat(session['check_in_time'])
        check_out_time = datetime.now()
        duration = int((check_out_time - check_in_time).total_seconds() / 60)
        
        # Update session
        conn.execute('''
            UPDATE sessions 
            SET check_out_time = ?, check_out_method = 'barcode', 
                duration_minutes = ?, is_active = 0
            WHERE id = ?
        ''', (check_out_time, duration, session['id']))
        
        # Update seat status
        conn.execute('UPDATE seats SET is_occupied = 0 WHERE id = ?', (session['seat_id'],))
        
        conn.commit()
        
        log_activity(session['user_id'], 'CHECK_OUT', 
                    f"Checked out from seat {session['seat_number']}, Duration: {duration} minutes")
        conn.close()
        
        return jsonify({
            'message': 'Check-out successful',
            'seat_number': session['seat_number'],
            'duration_minutes': duration
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': 'Check-out failed'}), 500

@app.route('/api/sessions/active', methods=['GET'])
def get_active_sessions():
    """Get all active sessions"""
    conn = get_db_connection()
    sessions = conn.execute('''
        SELECT sess.*, u.name as user_name, u.student_id,
               s.seat_number, h.name as hall_name
        FROM sessions sess
        JOIN users u ON sess.user_id = u.id
        JOIN seats s ON sess.seat_id = s.id
        JOIN reading_halls h ON sess.hall_id = h.id
        WHERE sess.is_active = 1
        ORDER BY sess.check_in_time DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(session) for session in sessions])

# ==================== ANALYTICS APIs ====================

@app.route('/api/analytics/overview', methods=['GET'])
def get_analytics_overview():
    """Get system overview analytics"""
    conn = get_db_connection()
    
    # Total seats and occupied seats
    seats_stats = conn.execute('''
        SELECT COUNT(*) as total_seats,
               SUM(CASE WHEN is_occupied = 1 THEN 1 ELSE 0 END) as occupied_seats
        FROM seats WHERE is_available = 1
    ''').fetchone()
    
    # Active sessions today
    today = datetime.now().date()
    sessions_today = conn.execute('''
        SELECT COUNT(*) as sessions_today
        FROM sessions
        WHERE DATE(check_in_time) = ?
    ''', (today,)).fetchone()
    
    # Average session duration (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    avg_duration = conn.execute('''
        SELECT AVG(duration_minutes) as avg_duration
        FROM sessions
        WHERE check_out_time IS NOT NULL 
        AND check_in_time >= ?
    ''', (week_ago,)).fetchone()
    
    conn.close()
    
    return jsonify({
        'total_seats': seats_stats['total_seats'],
        'occupied_seats': seats_stats['occupied_seats'],
        'available_seats': seats_stats['total_seats'] - seats_stats['occupied_seats'],
        'occupancy_rate': round((seats_stats['occupied_seats'] / seats_stats['total_seats']) * 100, 2) if seats_stats['total_seats'] > 0 else 0,
        'sessions_today': sessions_today['sessions_today'],
        'avg_duration_minutes': round(avg_duration['avg_duration'], 2) if avg_duration['avg_duration'] else 0
    })

@app.route('/api/analytics/usage', methods=['GET'])
def get_usage_analytics():
    """Get detailed usage analytics"""
    days = request.args.get('days', 7, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    conn = get_db_connection()
    
    # Daily usage statistics
    daily_stats = conn.execute('''
        SELECT DATE(check_in_time) as date,
               COUNT(*) as total_sessions,
               AVG(duration_minutes) as avg_duration,
               MAX(duration_minutes) as max_duration
        FROM sessions
        WHERE check_in_time >= ?
        GROUP BY DATE(check_in_time)
        ORDER BY date DESC
    ''', (start_date,)).fetchall()
    
    # Hourly distribution
    hourly_stats = conn.execute('''
        SELECT strftime('%H', check_in_time) as hour,
               COUNT(*) as session_count
        FROM sessions
        WHERE check_in_time >= ?
        GROUP BY hour
        ORDER BY hour
    ''', (start_date,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'daily_stats': [dict(stat) for stat in daily_stats],
        'hourly_stats': [dict(stat) for stat in hourly_stats]
    })

# ==================== COMPUTER VISION Integration ====================

@app.route('/api/vision/detection', methods=['POST'])
def update_vision_detection():
    """Receive computer vision detection updates"""
    data = request.get_json()
    
    required_fields = ['seat_id', 'is_occupied', 'confidence']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    
    try:
        # Log the detection
        conn.execute('''
            INSERT INTO vision_detections (seat_id, is_occupied, confidence, image_path)
            VALUES (?, ?, ?, ?)
        ''', (data['seat_id'], data['is_occupied'], data['confidence'], data.get('image_path')))
        
        # Get current seat status
        current_seat = conn.execute('SELECT * FROM seats WHERE id = ?', (data['seat_id'],)).fetchone()
        
        # If vision detects empty seat but seat is marked occupied, check for auto-checkout
        if not data['is_occupied'] and current_seat['is_occupied']:
            # Check if there's an active session
            session = conn.execute('''
                SELECT * FROM sessions 
                WHERE seat_id = ? AND is_active = 1
            ''', (data['seat_id'],)).fetchone()
            
            if session:
                last_activity = datetime.fromisoformat(session['last_activity'])
                idle_minutes = (datetime.now() - last_activity).total_seconds() / 60
                
                # Check idle timeout configuration
                timeout_config = conn.execute('''
                    SELECT value FROM configurations 
                    WHERE key = 'idle_timeout_minutes'
                ''').fetchone()
                
                timeout_minutes = int(timeout_config['value']) if timeout_config else 30
                
                if idle_minutes > timeout_minutes:
                    # Auto checkout
                    check_out_time = datetime.now()
                    duration = int((check_out_time - datetime.fromisoformat(session['check_in_time'])).total_seconds() / 60)
                    
                    conn.execute('''
                        UPDATE sessions 
                        SET check_out_time = ?, check_out_method = 'timeout',
                            duration_minutes = ?, is_active = 0
                        WHERE id = ?
                    ''', (check_out_time, duration, session['id']))
                    
                    conn.execute('UPDATE seats SET is_occupied = 0 WHERE id = ?', (data['seat_id'],))
                    
                    log_activity(session['user_id'], 'AUTO_CHECKOUT', 
                               f"Auto checkout due to {idle_minutes:.1f} min idle time")
        
        # If vision detects occupied seat but seat is marked empty, update status
        elif data['is_occupied'] and not current_seat['is_occupied'] and data['confidence'] > 0.8:
            conn.execute('UPDATE seats SET is_occupied = 1 WHERE id = ?', (data['seat_id'],))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Detection processed successfully'})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': 'Failed to process detection'}), 500

# ==================== CONFIGURATION APIs ====================

@app.route('/api/config', methods=['GET'])
def get_configurations():
    """Get system configurations"""
    conn = get_db_connection()
    configs = conn.execute('SELECT * FROM configurations').fetchall()
    conn.close()
    return jsonify([dict(config) for config in configs])

@app.route('/api/config', methods=['PUT'])
def update_configuration():
    """Update system configuration"""
    data = request.get_json()
    
    if 'key' not in data or 'value' not in data:
        return jsonify({'error': 'Missing key or value'}), 400
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE configurations 
        SET value = ?, updated_at = CURRENT_TIMESTAMP
        WHERE key = ?
    ''', (data['value'], data['key']))
    
    if conn.total_changes == 0:
        # Insert if doesn't exist
        conn.execute('''
            INSERT INTO configurations (key, value, description)
            VALUES (?, ?, ?)
        ''', (data['key'], data['value'], data.get('description', '')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Configuration updated successfully'})

# ==================== DASHBOARD HTML (for testing) ====================

@app.route('/')
def dashboard():
    """Simple HTML dashboard for testing"""
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SudarshanView Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .stats { display: flex; gap: 20px; margin: 20px 0; }
            .stat-card { padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .seats-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 5px; margin: 20px 0; }
            .seat { width: 40px; height: 40px; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center; }
            .seat.occupied { background-color: #ff6b6b; color: white; }
            .seat.available { background-color: #51cf66; }
        </style>
    </head>
    <body>
        <h1>SudarshanView Dashboard</h1>
        <div id="stats" class="stats"></div>
        <h2>Seat Layout</h2>
        <div id="seats" class="seats-grid"></div>
        <h2>Active Sessions</h2>
        <div id="sessions"></div>
        
        <script>
            async function loadDashboard() {
                // Load statistics
                const statsResponse = await fetch('/api/analytics/overview');
                const stats = await statsResponse.json();
                
                document.getElementById('stats').innerHTML = `
                    <div class="stat-card">
                        <h3>Total Seats</h3>
                        <p>${stats.total_seats}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Occupied</h3>
                        <p>${stats.occupied_seats}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Available</h3>
                        <p>${stats.available_seats}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Occupancy Rate</h3>
                        <p>${stats.occupancy_rate}%</p>
                    </div>
                `;
                
                // Load seats (assuming hall_id = 1)
                const seatsResponse = await fetch('/api/halls/1/seats');
                const seats = await seatsResponse.json();
                
                const seatsHtml = seats.map(seat => 
                    `<div class="seat ${seat.is_occupied ? 'occupied' : 'available'}">${seat.seat_number}</div>`
                ).join('');
                
                document.getElementById('seats').innerHTML = seatsHtml;
                
                // Load active sessions
                const sessionsResponse = await fetch('/api/sessions/active');
                const sessions = await sessionsResponse.json();
                
                const sessionsHtml = sessions.map(session => 
                    `<p>${session.user_name} - ${session.seat_number} (${session.check_in_time})</p>`
                ).join('');
                
                document.getElementById('sessions').innerHTML = sessionsHtml;
            }
            
            loadDashboard();
            setInterval(loadDashboard, 30000); // Refresh every 30 seconds
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

# ==================== BACKGROUND TASKS ====================

def cleanup_expired_sessions():
    """Background task to cleanup expired sessions"""
    while True:
        try:
            conn = get_db_connection()
            
            # Get max session hours configuration
            config = conn.execute('SELECT value FROM configurations WHERE key = "max_session_hours"').fetchone()
            max_hours = int(config['value']) if config else 8
            
            # Find expired sessions
            cutoff_time = datetime.now() - timedelta(hours=max_hours)
            expired_sessions = conn.execute('''
                SELECT * FROM sessions 
                WHERE is_active = 1 AND check_in_time < ?
            ''', (cutoff_time,)).fetchall()
            
            for session in expired_sessions:
                # Auto checkout expired sessions
                check_out_time = datetime.now()
                duration = int((check_out_time - datetime.fromisoformat(session['check_in_time'])).total_seconds() / 60)
                
                conn.execute('''
                    UPDATE sessions 
                    SET check_out_time = ?, check_out_method = 'expired',
                        duration_minutes = ?, is_active = 0
                    WHERE id = ?
                ''', (check_out_time, duration, session['id']))
                
                conn.execute('UPDATE seats SET is_occupied = 0 WHERE id = ?', (session['seat_id'],))
                
                log_activity(session['user_id'], 'SESSION_EXPIRED', f"Session expired after {max_hours} hours")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error in cleanup task: {e}")
        
        time.sleep(300)  # Run every 5 minutes

if __name__ == '__main__':
    # Start background cleanup task
    cleanup_thread = threading.Thread(target=cleanup_expired_sessions, daemon=True)
    cleanup_thread.start()
    
    # Start Flask application
    app.run(host='0.0.0.0', port=5000, debug=True)
