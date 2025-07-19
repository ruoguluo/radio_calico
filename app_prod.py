import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import hashlib
from datetime import datetime
import logging
import psycopg2
from urllib.parse import urlparse

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Configure CORS for production
CORS(app, origins=os.getenv('ALLOWED_ORIGINS', '*').split(','))

# Database configuration
# Use PostgreSQL in production, SQLite in development
if os.getenv('DATABASE_URL'):
    # Production: PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    USE_POSTGRES = True
else:
    # Development: SQLite
    database_path = os.getenv('DATABASE_PATH', '/app/data/database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    USE_POSTGRES = False

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class SongRating(db.Model):
    __tablename__ = 'song_ratings'
    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.String(100), nullable=False)
    user_fingerprint = db.Column(db.String(32), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('song_id', 'user_fingerprint'),
        db.CheckConstraint('rating IN (1, -1)')
    )

def init_db():
    try:
        with app.app_context():
            # Test database connection
            if USE_POSTGRES:
                # Test PostgreSQL connection
                result = db.session.execute(text('SELECT 1'))
                result.fetchone()
                logging.info("PostgreSQL connection established")
            else:
                # For SQLite, ensure directory exists
                db_path = os.getenv('DATABASE_PATH', '/app/data/database.db')
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                logging.info(f"SQLite database at {db_path}")
            
            # Create tables
            db.create_all()
            logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        raise

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
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        return jsonify({
            'users': [{
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'created_at': user.created_at.isoformat()
            } for user in users]
        })
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'email' not in data:
            return jsonify({'error': 'Name and email are required'}), 400
        
        # Basic input validation
        name = str(data['name']).strip()[:100]  # Limit length
        email = str(data['email']).strip()[:100]
        
        if not name or not email:
            return jsonify({'error': 'Name and email cannot be empty'}), 400
        
        # Basic email format validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(name=name, email=email)
        db.session.add(user)
        db.session.commit()
        
        logging.info(f"User created: {user.id} - {email}")
        return jsonify({
            'id': user.id,
            'message': 'User created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating user: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def generate_user_fingerprint(request):
    user_agent = request.headers.get('User-Agent', '')[:500]  # Limit length
    ip_address = request.remote_addr or ''
    # Use X-Forwarded-For if behind proxy
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    fingerprint_data = f"{user_agent}_{ip_address}"
    return hashlib.md5(fingerprint_data.encode()).hexdigest()

@app.route('/api/ratings/<song_id>', methods=['GET'])
def get_ratings(song_id):
    try:
        # Sanitize song_id
        song_id = str(song_id)[:100]
        
        # Get rating counts
        thumbs_up = SongRating.query.filter_by(song_id=song_id, rating=1).count()
        thumbs_down = SongRating.query.filter_by(song_id=song_id, rating=-1).count()
        
        # Get user's rating
        user_fingerprint = generate_user_fingerprint(request)
        user_rating = SongRating.query.filter_by(
            song_id=song_id, 
            user_fingerprint=user_fingerprint
        ).first()
        
        return jsonify({
            'song_id': song_id,
            'thumbs_up': thumbs_up,
            'thumbs_down': thumbs_down,
            'user_rating': user_rating.rating if user_rating else None
        })
    except Exception as e:
        logging.error(f"Error fetching ratings for {song_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ratings/<song_id>', methods=['POST'])
def rate_song(song_id):
    try:
        # Sanitize song_id
        song_id = str(song_id)[:100]
        
        data = request.get_json()
        if not data or 'rating' not in data:
            return jsonify({'error': 'Rating is required'}), 400
        
        rating = int(data['rating'])
        if rating not in [1, -1]:
            return jsonify({'error': 'Rating must be 1 (thumbs up) or -1 (thumbs down)'}), 400
        
        user_fingerprint = generate_user_fingerprint(request)
        
        # Check if user already rated this song
        existing_rating = SongRating.query.filter_by(
            song_id=song_id, 
            user_fingerprint=user_fingerprint
        ).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            existing_rating.created_at = datetime.utcnow()
            message = 'Rating updated successfully'
        else:
            # Create new rating
            new_rating = SongRating(
                song_id=song_id,
                user_fingerprint=user_fingerprint,
                rating=rating
            )
            db.session.add(new_rating)
            message = 'Rating submitted successfully'
        
        db.session.commit()
        
        # Get updated rating counts
        thumbs_up = SongRating.query.filter_by(song_id=song_id, rating=1).count()
        thumbs_down = SongRating.query.filter_by(song_id=song_id, rating=-1).count()
        
        logging.info(f"Rating submitted for {song_id}: {rating}")
        return jsonify({
            'message': message,
            'song_id': song_id,
            'thumbs_up': thumbs_up,
            'thumbs_down': thumbs_down,
            'user_rating': rating
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid rating value'}), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error rating song {song_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for load balancers"""
    try:
        # Quick database check
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy', 
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'postgresql' if USE_POSTGRES else 'sqlite'
        }), 200
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    init_db()
    
    # Development server
    if os.getenv('FLASK_ENV') == 'development':
        app.run(debug=True, host='0.0.0.0', port=3000)
    else:
        # Production should use gunicorn
        logging.info("Starting Radio Russell in production mode")
        app.run(host='0.0.0.0', port=8000)
