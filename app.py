from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import hashlib
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS song_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id TEXT NOT NULL,
            user_fingerprint TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating IN (1, -1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(song_id, user_fingerprint)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/test')
def test_page():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return jsonify({
        'users': [dict(user) for user in users]
    })

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({'error': 'Name and email are required'}), 400
    
    name = data['name']
    email = data['email']
    
    try:
        conn = get_db_connection()
        cursor = conn.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': user_id,
            'message': 'User created successfully'
        }), 201
    
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_user_fingerprint(request):
    user_agent = request.headers.get('User-Agent', '')
    ip_address = request.remote_addr or ''
    fingerprint_data = f"{user_agent}_{ip_address}"
    return hashlib.md5(fingerprint_data.encode()).hexdigest()

@app.route('/api/ratings/<song_id>', methods=['GET'])
def get_ratings(song_id):
    try:
        conn = get_db_connection()
        ratings = conn.execute('''
            SELECT 
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as thumbs_down
            FROM song_ratings WHERE song_id = ?
        ''', (song_id,)).fetchone()
        
        user_fingerprint = generate_user_fingerprint(request)
        user_rating = conn.execute('''
            SELECT rating FROM song_ratings WHERE song_id = ? AND user_fingerprint = ?
        ''', (song_id, user_fingerprint)).fetchone()
        
        conn.close()
        
        return jsonify({
            'song_id': song_id,
            'thumbs_up': ratings['thumbs_up'] or 0,
            'thumbs_down': ratings['thumbs_down'] or 0,
            'user_rating': user_rating['rating'] if user_rating else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ratings/<song_id>', methods=['POST'])
def rate_song(song_id):
    try:
        data = request.get_json()
        if not data or 'rating' not in data:
            return jsonify({'error': 'Rating is required'}), 400
        
        rating = data['rating']
        if rating not in [1, -1]:
            return jsonify({'error': 'Rating must be 1 (thumbs up) or -1 (thumbs down)'}), 400
        
        user_fingerprint = generate_user_fingerprint(request)
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO song_ratings (song_id, user_fingerprint, rating)
                VALUES (?, ?, ?)
            ''', (song_id, user_fingerprint, rating))
            conn.commit()
            message = 'Rating submitted successfully'
        except sqlite3.IntegrityError:
            conn.execute('''
                UPDATE song_ratings SET rating = ?, created_at = CURRENT_TIMESTAMP
                WHERE song_id = ? AND user_fingerprint = ?
            ''', (rating, song_id, user_fingerprint))
            conn.commit()
            message = 'Rating updated successfully'
        
        # Get updated ratings
        ratings = conn.execute('''
            SELECT 
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as thumbs_down
            FROM song_ratings WHERE song_id = ?
        ''', (song_id,)).fetchone()
        
        conn.close()
        
        return jsonify({
            'message': message,
            'song_id': song_id,
            'thumbs_up': ratings['thumbs_up'] or 0,
            'thumbs_down': ratings['thumbs_down'] or 0,
            'user_rating': rating
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    print(f"Database initialized at {DATABASE}")
    app.run(debug=True, host='0.0.0.0', port=3000)