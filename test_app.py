import json
import os
import tempfile
import unittest

from app import app, generate_user_fingerprint, get_db_connection, init_db


class RadioCalicoTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary database file
        self.db_fd, app.config["DATABASE"] = tempfile.mkstemp()
        app.config["TESTING"] = True
        self.client = app.test_client()

        # Initialize the test database
        with app.app_context():
            # Temporarily override the DATABASE constant
            import app as app_module

            self.original_database = app_module.DATABASE
            app_module.DATABASE = app.config["DATABASE"]
            init_db()

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original database path
        import app as app_module

        app_module.DATABASE = self.original_database

        # Close and remove the temporary database file
        os.close(self.db_fd)
        os.unlink(app.config["DATABASE"])

    def test_home_route(self):
        """Test the home route returns the main HTML page."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Radio Calico", response.data)

    def test_test_page_route(self):
        """Test the test page route serves static HTML."""
        response = self.client.get("/test")
        self.assertEqual(response.status_code, 200)

    def test_static_files(self):
        """Test serving static files."""
        # This will return 404 if file doesn't exist, but route should work
        response = self.client.get("/static/nonexistent.js")
        # We expect 404 for non-existent file, but route should be accessible
        self.assertIn(response.status_code, [200, 404])

    def test_get_users_empty(self):
        """Test getting users when database is empty."""
        response = self.client.get("/api/users")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("users", data)
        self.assertEqual(len(data["users"]), 0)

    def test_create_user_success(self):
        """Test creating a user successfully."""
        user_data = {"name": "John Doe", "email": "john@example.com"}
        response = self.client.post(
            "/api/users", data=json.dumps(user_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn("id", data)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "User created successfully")

    def test_create_user_missing_data(self):
        """Test creating a user with missing required fields."""
        # Missing email
        user_data = {"name": "John Doe"}
        response = self.client.post(
            "/api/users", data=json.dumps(user_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Name and email are required")

    def test_create_user_duplicate_email(self):
        """Test creating a user with duplicate email."""
        user_data = {"name": "John Doe", "email": "john@example.com"}

        # Create first user
        response1 = self.client.post(
            "/api/users", data=json.dumps(user_data), content_type="application/json"
        )
        self.assertEqual(response1.status_code, 201)

        # Try to create second user with same email
        user_data["name"] = "Jane Doe"
        response2 = self.client.post(
            "/api/users", data=json.dumps(user_data), content_type="application/json"
        )

        self.assertEqual(response2.status_code, 400)
        data = json.loads(response2.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Email already exists")

    def test_create_user_invalid_json(self):
        """Test creating a user with invalid JSON."""
        response = self.client.post(
            "/api/users", data="invalid json", content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)

    def test_get_users_after_creation(self):
        """Test getting users after creating some."""
        # Create a test user
        user_data = {"name": "John Doe", "email": "john@example.com"}
        self.client.post(
            "/api/users", data=json.dumps(user_data), content_type="application/json"
        )

        # Get users
        response = self.client.get("/api/users")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertIn("users", data)
        self.assertEqual(len(data["users"]), 1)
        self.assertEqual(data["users"][0]["name"], "John Doe")
        self.assertEqual(data["users"][0]["email"], "john@example.com")

    def test_get_ratings_nonexistent_song(self):
        """Test getting ratings for a song that doesn't exist."""
        response = self.client.get("/api/ratings/nonexistent_song")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data["song_id"], "nonexistent_song")
        self.assertEqual(data["thumbs_up"], 0)
        self.assertEqual(data["thumbs_down"], 0)
        self.assertIsNone(data["user_rating"])

    def test_rate_song_thumbs_up(self):
        """Test rating a song with thumbs up."""
        song_id = "test_song_123"
        rating_data = {"rating": 1}

        response = self.client.post(
            f"/api/ratings/{song_id}",
            data=json.dumps(rating_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data["song_id"], song_id)
        self.assertEqual(data["thumbs_up"], 1)
        self.assertEqual(data["thumbs_down"], 0)
        self.assertEqual(data["user_rating"], 1)
        self.assertIn("message", data)

    def test_rate_song_thumbs_down(self):
        """Test rating a song with thumbs down."""
        song_id = "test_song_123"
        rating_data = {"rating": -1}

        response = self.client.post(
            f"/api/ratings/{song_id}",
            data=json.dumps(rating_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data["song_id"], song_id)
        self.assertEqual(data["thumbs_up"], 0)
        self.assertEqual(data["thumbs_down"], 1)
        self.assertEqual(data["user_rating"], -1)

    def test_rate_song_invalid_rating(self):
        """Test rating a song with invalid rating value."""
        song_id = "test_song_123"
        rating_data = {"rating": 5}  # Invalid rating

        response = self.client.post(
            f"/api/ratings/{song_id}",
            data=json.dumps(rating_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(
            data["error"], "Rating must be 1 (thumbs up) or -1 (thumbs down)"
        )

    def test_rate_song_missing_rating(self):
        """Test rating a song without providing rating data."""
        song_id = "test_song_123"
        rating_data = {}  # Missing rating

        response = self.client.post(
            f"/api/ratings/{song_id}",
            data=json.dumps(rating_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Rating is required")

    def test_update_existing_rating(self):
        """Test updating an existing rating for the same user."""
        song_id = "test_song_123"

        # First rating: thumbs up
        rating_data = {"rating": 1}
        response1 = self.client.post(
            f"/api/ratings/{song_id}",
            data=json.dumps(rating_data),
            content_type="application/json",
        )
        self.assertEqual(response1.status_code, 200)
        data1 = json.loads(response1.data)
        self.assertEqual(data1["thumbs_up"], 1)
        self.assertEqual(data1["thumbs_down"], 0)

        # Update to thumbs down
        rating_data = {"rating": -1}
        response2 = self.client.post(
            f"/api/ratings/{song_id}",
            data=json.dumps(rating_data),
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 200)
        data2 = json.loads(response2.data)

        # Should show updated counts
        self.assertEqual(data2["thumbs_up"], 0)
        self.assertEqual(data2["thumbs_down"], 1)
        self.assertEqual(data2["user_rating"], -1)
        self.assertIn("updated successfully", data2["message"])

    def test_get_ratings_after_voting(self):
        """Test getting ratings after some votes have been cast."""
        song_id = "test_song_123"

        # Rate the song
        rating_data = {"rating": 1}
        self.client.post(
            f"/api/ratings/{song_id}",
            data=json.dumps(rating_data),
            content_type="application/json",
        )

        # Get ratings
        response = self.client.get(f"/api/ratings/{song_id}")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data["song_id"], song_id)
        self.assertEqual(data["thumbs_up"], 1)
        self.assertEqual(data["thumbs_down"], 0)
        self.assertEqual(data["user_rating"], 1)

    def test_user_fingerprinting(self):
        """Test user fingerprint generation."""
        with app.test_request_context("/", headers={"User-Agent": "Test Browser"}):
            fingerprint1 = generate_user_fingerprint(app.test_request_context().request)
            fingerprint2 = generate_user_fingerprint(app.test_request_context().request)

            # Same request should generate same fingerprint
            self.assertEqual(fingerprint1, fingerprint2)
            self.assertIsInstance(fingerprint1, str)
            self.assertEqual(len(fingerprint1), 32)  # MD5 hash length

    def test_database_connection(self):
        """Test database connection functionality."""
        with app.app_context():
            import app as app_module

            app_module.DATABASE = app.config["DATABASE"]
            conn = get_db_connection()
            self.assertIsNotNone(conn)

            # Test that tables exist
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]

            self.assertIn("users", table_names)
            self.assertIn("song_ratings", table_names)
            conn.close()


class DatabaseIntegrityTestCase(unittest.TestCase):
    """Test database constraints and integrity."""

    def setUp(self):
        self.db_fd, app.config["DATABASE"] = tempfile.mkstemp()
        app.config["TESTING"] = True
        self.client = app.test_client()

        with app.app_context():
            import app as app_module

            self.original_database = app_module.DATABASE
            app_module.DATABASE = app.config["DATABASE"]
            init_db()

    def tearDown(self):
        import app as app_module

        app_module.DATABASE = self.original_database
        os.close(self.db_fd)
        os.unlink(app.config["DATABASE"])

    def test_unique_constraint_song_ratings(self):
        """Test that the unique constraint on song_ratings works."""
        with app.app_context():
            import app as app_module

            app_module.DATABASE = app.config["DATABASE"]

            conn = get_db_connection()

            # Insert first rating
            conn.execute(
                """
                INSERT INTO song_ratings (song_id, user_fingerprint, rating)
                VALUES (?, ?, ?)
            """,
                ("test_song", "test_user", 1),
            )
            conn.commit()

            # Try to insert duplicate - should fail
            with self.assertRaises(Exception):
                conn.execute(
                    """
                    INSERT INTO song_ratings (song_id, user_fingerprint, rating)
                    VALUES (?, ?, ?)
                """,
                    ("test_song", "test_user", -1),
                )
                conn.commit()

            conn.close()

    def test_rating_check_constraint(self):
        """Test that rating values are constrained to 1 and -1."""
        with app.app_context():
            import app as app_module

            app_module.DATABASE = app.config["DATABASE"]

            conn = get_db_connection()

            # Valid ratings should work
            conn.execute(
                """
                INSERT INTO song_ratings (song_id, user_fingerprint, rating)
                VALUES (?, ?, ?)
            """,
                ("test_song", "test_user1", 1),
            )

            conn.execute(
                """
                INSERT INTO song_ratings (song_id, user_fingerprint, rating)
                VALUES (?, ?, ?)
            """,
                ("test_song", "test_user2", -1),
            )
            conn.commit()

            # Invalid rating should fail
            with self.assertRaises(Exception):
                conn.execute(
                    """
                    INSERT INTO song_ratings (song_id, user_fingerprint, rating)
                    VALUES (?, ?, ?)
                """,
                    ("test_song", "test_user3", 0),
                )
                conn.commit()

            conn.close()


if __name__ == "__main__":
    # Create a test suite
    suite = unittest.TestSuite()

    # Add all test methods from RadioCalicoTestCase
    suite.addTest(unittest.makeSuite(RadioCalicoTestCase))
    suite.addTest(unittest.makeSuite(DatabaseIntegrityTestCase))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
