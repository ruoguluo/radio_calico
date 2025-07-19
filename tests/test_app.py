import pytest
import json
from app_prod import User, SongRating, db


class TestHealthEndpoint:
    """Tests for the health endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint returns success."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'database' in data


class TestUserAPI:
    """Tests for user management API."""
    
    def test_get_empty_users(self, client):
        """Test getting users when none exist."""
        response = client.get('/api/users')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['users'] == []
    
    def test_create_user(self, client, app_context):
        """Test creating a new user."""
        user_data = {
            'name': 'Test User',
            'email': 'test@example.com'
        }
        
        response = client.post('/api/users', 
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'User created successfully'
        assert 'id' in data
    
    def test_create_user_duplicate_email(self, client, app_context):
        """Test creating user with duplicate email fails."""
        user_data = {
            'name': 'Test User',
            'email': 'duplicate@example.com'
        }
        
        # Create first user
        response1 = client.post('/api/users',
                              data=json.dumps(user_data),
                              content_type='application/json')
        assert response1.status_code == 201
        
        # Try to create second user with same email
        response2 = client.post('/api/users',
                              data=json.dumps(user_data),
                              content_type='application/json')
        assert response2.status_code == 400
        
        data = json.loads(response2.data)
        assert 'already exists' in data['error'].lower()
    
    def test_create_user_invalid_data(self, client):
        """Test creating user with invalid data fails."""
        # Missing email
        response = client.post('/api/users',
                             data=json.dumps({'name': 'Test'}),
                             content_type='application/json')
        assert response.status_code == 400
        
        # Missing name
        response = client.post('/api/users',
                             data=json.dumps({'email': 'test@example.com'}),
                             content_type='application/json')
        assert response.status_code == 400
        
        # Invalid email format
        response = client.post('/api/users',
                             data=json.dumps({'name': 'Test', 'email': 'invalid'}),
                             content_type='application/json')
        assert response.status_code == 400


class TestRatingsAPI:
    """Tests for song ratings API."""
    
    def test_get_ratings_nonexistent_song(self, client):
        """Test getting ratings for a song that doesn't exist."""
        response = client.get('/api/ratings/nonexistent_song')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['song_id'] == 'nonexistent_song'
        assert data['thumbs_up'] == 0
        assert data['thumbs_down'] == 0
        assert data['user_rating'] is None
    
    def test_submit_rating(self, client):
        """Test submitting a rating for a song."""
        rating_data = {'rating': 1}
        
        response = client.post('/api/ratings/test_song',
                             data=json.dumps(rating_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Rating submitted successfully'
        assert data['thumbs_up'] == 1
        assert data['thumbs_down'] == 0
        assert data['user_rating'] == 1
    
    def test_update_rating(self, client):
        """Test updating an existing rating."""
        song_id = 'update_test_song'
        
        # Submit initial rating
        response1 = client.post(f'/api/ratings/{song_id}',
                              data=json.dumps({'rating': 1}),
                              content_type='application/json')
        assert response1.status_code == 200
        
        # Update rating
        response2 = client.post(f'/api/ratings/{song_id}',
                              data=json.dumps({'rating': -1}),
                              content_type='application/json')
        assert response2.status_code == 200
        
        data = json.loads(response2.data)
        assert data['message'] == 'Rating updated successfully'
        assert data['thumbs_up'] == 0
        assert data['thumbs_down'] == 1
        assert data['user_rating'] == -1
    
    def test_invalid_rating(self, client):
        """Test submitting invalid rating fails."""
        # Invalid rating value
        response = client.post('/api/ratings/test_song',
                             data=json.dumps({'rating': 5}),
                             content_type='application/json')
        assert response.status_code == 400
        
        # Missing rating
        response = client.post('/api/ratings/test_song',
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 400


class TestDatabaseModels:
    """Tests for database models."""
    
    def test_user_model(self, app_context):
        """Test User model creation and properties."""
        user = User(name='Test User', email='model@test.com')
        db.session.add(user)
        db.session.commit()
        
        # Test user was created
        assert user.id is not None
        assert user.name == 'Test User'
        assert user.email == 'model@test.com'
        assert user.created_at is not None
        
        # Test user can be retrieved
        retrieved_user = User.query.filter_by(email='model@test.com').first()
        assert retrieved_user is not None
        assert retrieved_user.name == 'Test User'
    
    def test_song_rating_model(self, app_context):
        """Test SongRating model creation and properties."""
        rating = SongRating(
            song_id='test_song_123',
            user_fingerprint='test_fingerprint',
            rating=1
        )
        db.session.add(rating)
        db.session.commit()
        
        # Test rating was created
        assert rating.id is not None
        assert rating.song_id == 'test_song_123'
        assert rating.user_fingerprint == 'test_fingerprint'
        assert rating.rating == 1
        assert rating.created_at is not None
        
        # Test rating can be retrieved
        retrieved_rating = SongRating.query.filter_by(song_id='test_song_123').first()
        assert retrieved_rating is not None
        assert retrieved_rating.rating == 1


class TestErrorHandlers:
    """Tests for error handling."""
    
    def test_404_error(self, client):
        """Test 404 error handler."""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
