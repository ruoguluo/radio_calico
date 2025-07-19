import pytest
import os
import tempfile
from flask import Flask


def create_test_app():
    """Create a test Flask application."""
    from flask_sqlalchemy import SQLAlchemy
    from flask_cors import CORS
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure for testing
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL', f'sqlite:///{db_path}'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
    })
    
    # Initialize extensions
    db = SQLAlchemy(app)
    CORS(app)
    
    # Import models to register them
    with app.app_context():
        # Define models here to avoid import issues
        from datetime import datetime
        import hashlib
        
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
        
        # Add models to app for access in tests
        app.User = User
        app.SongRating = SongRating
        app.db = db
        
        # Create routes (simplified versions)
        @app.route('/health')
        def health_check():
            from flask import jsonify
            try:
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                return jsonify({
                    'status': 'healthy', 
                    'timestamp': datetime.utcnow().isoformat(),
                    'database': 'sqlite'
                }), 200
            except Exception as e:
                return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
        
        @app.route('/api/users', methods=['GET'])
        def get_users():
            from flask import jsonify
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
                return jsonify({'error': 'Internal server error'}), 500
        
        @app.route('/api/users', methods=['POST'])
        def create_user():
            from flask import request, jsonify
            try:
                data = request.get_json()
                
                if not data or 'name' not in data or 'email' not in data:
                    return jsonify({'error': 'Name and email are required'}), 400
                
                name = str(data['name']).strip()[:100]
                email = str(data['email']).strip()[:100]
                
                if not name or not email:
                    return jsonify({'error': 'Name and email cannot be empty'}), 400
                
                if '@' not in email or '.' not in email.split('@')[-1]:
                    return jsonify({'error': 'Invalid email format'}), 400
                
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    return jsonify({'error': 'Email already exists'}), 400
                
                user = User(name=name, email=email)
                db.session.add(user)
                db.session.commit()
                
                return jsonify({
                    'id': user.id,
                    'message': 'User created successfully'
                }), 201
            
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': 'Internal server error'}), 500
        
        def generate_user_fingerprint(request):
            user_agent = request.headers.get('User-Agent', '')[:500]
            ip_address = request.remote_addr or ''
            if request.headers.get('X-Forwarded-For'):
                ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
            fingerprint_data = f"{user_agent}_{ip_address}"
            return hashlib.md5(fingerprint_data.encode()).hexdigest()
        
        @app.route('/api/ratings/<song_id>', methods=['GET'])
        def get_ratings(song_id):
            from flask import jsonify, request
            try:
                song_id = str(song_id)[:100]
                thumbs_up = SongRating.query.filter_by(song_id=song_id, rating=1).count()
                thumbs_down = SongRating.query.filter_by(song_id=song_id, rating=-1).count()
                
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
                return jsonify({'error': 'Internal server error'}), 500
        
        @app.route('/api/ratings/<song_id>', methods=['POST'])
        def rate_song(song_id):
            from flask import request, jsonify
            try:
                song_id = str(song_id)[:100]
                data = request.get_json()
                
                if not data or 'rating' not in data:
                    return jsonify({'error': 'Rating is required'}), 400
                
                rating = int(data['rating'])
                if rating not in [1, -1]:
                    return jsonify({'error': 'Rating must be 1 (thumbs up) or -1 (thumbs down)'}), 400
                
                user_fingerprint = generate_user_fingerprint(request)
                
                existing_rating = SongRating.query.filter_by(
                    song_id=song_id, 
                    user_fingerprint=user_fingerprint
                ).first()
                
                if existing_rating:
                    existing_rating.rating = rating
                    existing_rating.created_at = datetime.utcnow()
                    message = 'Rating updated successfully'
                else:
                    new_rating = SongRating(
                        song_id=song_id,
                        user_fingerprint=user_fingerprint,
                        rating=rating
                    )
                    db.session.add(new_rating)
                    message = 'Rating submitted successfully'
                
                db.session.commit()
                
                thumbs_up = SongRating.query.filter_by(song_id=song_id, rating=1).count()
                thumbs_down = SongRating.query.filter_by(song_id=song_id, rating=-1).count()
                
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
                return jsonify({'error': 'Internal server error'}), 500
        
        @app.errorhandler(404)
        def not_found(error):
            from flask import jsonify
            return jsonify({'error': 'Not found'}), 404
        
        # Create database tables
        db.create_all()
    
    return app, db_path


@pytest.fixture(scope='session')
def test_app():
    """Create and configure a test app instance."""
    app, db_path = create_test_app()
    
    yield app
    
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def client(test_app):
    """Create a test client for the app."""
    return test_app.test_client()


@pytest.fixture
def app_context(test_app):
    """Create an application context."""
    with test_app.app_context():
        yield test_app
