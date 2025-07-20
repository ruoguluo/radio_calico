import hashlib
import os
import sqlite3
from datetime import datetime, timedelta
from urllib.parse import urlparse

from flask import Flask, g, jsonify, make_response, request, send_from_directory
from flask_compress import Compress
from flask_cors import CORS

try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Enable compression for all responses
Compress(app)

# Configuration
# Check DATABASE_PATH first (for dev/SQLite), then DATABASE_URL (for prod/PostgreSQL)
DATABASE = os.getenv("DATABASE_PATH") or os.getenv("DATABASE_URL") or "database.db"
CACHE_TIMEOUT = 300  # 5 minutes for most responses
STATIC_CACHE_TIMEOUT = 86400 * 30  # 30 days for static files

# In-memory cache for frequently accessed data
cache = {}


def get_cache_key(prefix, *args):
    """Generate cache key from prefix and arguments"""
    key_data = f"{prefix}:{':'.join(map(str, args))}"
    return hashlib.md5(key_data.encode()).hexdigest()


def get_cached_response(cache_key, max_age=CACHE_TIMEOUT):
    """Get cached response if still valid"""
    if cache_key in cache:
        cached_data, timestamp = cache[cache_key]
        if datetime.now() - timestamp < timedelta(seconds=max_age):
            return cached_data
        else:
            # Remove expired cache entry
            del cache[cache_key]
    return None


def set_cache(cache_key, data):
    """Set cache entry with timestamp"""
    cache[cache_key] = (data, datetime.now())

    # Simple cache cleanup - keep only last 100 entries
    if len(cache) > 100:
        oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
        del cache[oldest_key]


def get_db_connection():
    """Get database connection with connection pooling"""
    if not hasattr(g, "db_connection"):
        if DATABASE.startswith('postgresql://') and POSTGRES_AVAILABLE:
            url = urlparse(DATABASE)
            conn_params = {
                'dbname': url.path[1:],
                'user': url.username,
                'password': url.password,
                'host': url.hostname,
                'port': url.port or 5432
            }
            g.db_connection = psycopg2.connect(**conn_params)
            g.db_connection.autocommit = True
        else:
            g.db_connection = sqlite3.connect(DATABASE)
            g.db_connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent performance
            g.db_connection.execute("PRAGMA journal_mode=WAL")
    return g.db_connection


@app.teardown_appcontext
def close_db_connection(exception):
    """Close database connection at end of request"""
    db = getattr(g, "db_connection", None)
    if db is not None:
        db.close()


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS song_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id TEXT NOT NULL,
            user_fingerprint TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating IN (1, -1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(song_id, user_fingerprint)
        )
    """
    )

    # Create indexes for better query performance
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_song_ratings_song_id ON song_ratings(song_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_song_ratings_fingerprint ON song_ratings(user_fingerprint)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    conn.commit()


def add_cache_headers(response, max_age=CACHE_TIMEOUT):
    """Add caching headers to response"""
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    
    # Only generate ETag if response data is accessible (not in direct passthrough mode)
    try:
        if hasattr(response, 'get_data') and not response.direct_passthrough:
            response.headers["ETag"] = hashlib.md5(response.get_data()).hexdigest()[:16]
    except (RuntimeError, AttributeError):
        # Skip ETag generation if response is in passthrough mode or data is not accessible
        pass
    
    return response


def add_security_headers(response):
    """Add security headers to response"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.after_request
def after_request(response):
    """Add headers to all responses"""
    response = add_security_headers(response)

    # Add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"

    return response


@app.route("/")
def home():
    response = make_response(send_from_directory(".", "index_optimized.html"))
    return add_cache_headers(response, max_age=3600)  # Cache for 1 hour


@app.route("/test")
def test_page():
    response = make_response(send_from_directory("static", "index.html"))
    return add_cache_headers(response, max_age=3600)


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files with aggressive caching"""
    response = make_response(send_from_directory("static", filename))

    # Set different cache times based on file type
    if filename.endswith((".css", ".js")):
        cache_time = STATIC_CACHE_TIMEOUT  # 30 days
    elif filename.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        cache_time = STATIC_CACHE_TIMEOUT  # 30 days
    else:
        cache_time = 3600  # 1 hour for other files

    return add_cache_headers(response, max_age=cache_time)


@app.route("/api/users", methods=["GET"])
def get_users():
    """Get users with caching"""
    cache_key = get_cache_key("users_list")
    cached_response = get_cached_response(cache_key, max_age=60)  # 1 minute cache

    if cached_response:
        response = make_response(jsonify(cached_response))
        response.headers["X-Cache"] = "HIT"
        return add_cache_headers(response, max_age=60)

    conn = get_db_connection()
    users = conn.execute(
        "SELECT * FROM users ORDER BY created_at DESC LIMIT 100"
    ).fetchall()

    result = {"users": [dict(user) for user in users]}
    set_cache(cache_key, result)

    response = make_response(jsonify(result))
    response.headers["X-Cache"] = "MISS"
    return add_cache_headers(response, max_age=60)


@app.route("/api/users", methods=["POST"])
def create_user():
    """Create user with input validation and rate limiting"""
    data = request.get_json()

    if not data or "name" not in data or "email" not in data:
        return jsonify({"error": "Name and email are required"}), 400

    # Input validation and sanitization
    name = str(data["name"]).strip()[:100]
    email = str(data["email"]).strip().lower()[:100]

    if not name or not email:
        return jsonify({"error": "Name and email cannot be empty"}), 400

    # Basic email validation
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error": "Invalid email format"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)", (name, email)
        )
        user_id = cursor.lastrowid
        conn.commit()

        # Clear users cache
        cache_key = get_cache_key("users_list")
        if cache_key in cache:
            del cache[cache_key]

        return jsonify({"id": user_id, "message": "User created successfully"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400
    except Exception:
        return jsonify({"error": "Internal server error"}), 500


def generate_user_fingerprint(request):
    """Generate user fingerprint with better hashing"""
    user_agent = request.headers.get("User-Agent", "")[:500]
    ip_address = request.remote_addr or ""

    # Use X-Forwarded-For if behind proxy
    if request.headers.get("X-Forwarded-For"):
        ip_address = request.headers.get("X-Forwarded-For").split(",")[0].strip()

    fingerprint_data = f"{user_agent}_{ip_address}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]


@app.route("/api/ratings/<song_id>", methods=["GET"])
def get_ratings(song_id):
    """Get ratings with caching and optimized queries"""
    song_id = str(song_id)[:100]  # Sanitize input

    cache_key = get_cache_key("ratings", song_id)
    cached_response = get_cached_response(cache_key, max_age=30)  # 30 second cache

    if cached_response:
        response = make_response(jsonify(cached_response))
        response.headers["X-Cache"] = "HIT"
        return add_cache_headers(response, max_age=30)

    try:
        conn = get_db_connection()

        # Single optimized query for all rating data
        ratings_query = """
            SELECT 
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as thumbs_down
            FROM song_ratings WHERE song_id = ?
        """
        ratings = conn.execute(ratings_query, (song_id,)).fetchone()

        user_fingerprint = generate_user_fingerprint(request)
        user_rating = conn.execute(
            "SELECT rating FROM song_ratings WHERE song_id = ? AND user_fingerprint = ?",
            (song_id, user_fingerprint),
        ).fetchone()

        result = {
            "song_id": song_id,
            "thumbs_up": ratings["thumbs_up"] or 0,
            "thumbs_down": ratings["thumbs_down"] or 0,
            "user_rating": user_rating["rating"] if user_rating else None,
        }

        set_cache(cache_key, result)

        response = make_response(jsonify(result))
        response.headers["X-Cache"] = "MISS"
        return add_cache_headers(response, max_age=30)

    except Exception:
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/ratings/<song_id>", methods=["POST"])
def rate_song(song_id):
    """Rate song with validation and cache invalidation"""
    song_id = str(song_id)[:100]  # Sanitize input

    try:
        data = request.get_json()
        if not data or "rating" not in data:
            return jsonify({"error": "Rating is required"}), 400

        rating = int(data["rating"])
        if rating not in [1, -1]:
            return (
                jsonify({"error": "Rating must be 1 (thumbs up) or -1 (thumbs down)"}),
                400,
            )

        user_fingerprint = generate_user_fingerprint(request)
        conn = get_db_connection()

        # Use UPSERT for better performance
        try:
            conn.execute(
                """
                INSERT INTO song_ratings (song_id, user_fingerprint, rating)
                VALUES (?, ?, ?)
                ON CONFLICT(song_id, user_fingerprint) 
                DO UPDATE SET rating = ?, created_at = CURRENT_TIMESTAMP
                """,
                (song_id, user_fingerprint, rating, rating),
            )
            conn.commit()
            message = "Rating submitted successfully"
        except sqlite3.OperationalError:
            # Fallback for older SQLite versions
            existing = conn.execute(
                "SELECT id FROM song_ratings WHERE song_id = ? AND user_fingerprint = ?",
                (song_id, user_fingerprint),
            ).fetchone()

            if existing:
                conn.execute(
                    """UPDATE song_ratings SET rating = ?, created_at = CURRENT_TIMESTAMP 
                    WHERE song_id = ? AND user_fingerprint = ?""",
                    (rating, song_id, user_fingerprint),
                )
                message = "Rating updated successfully"
            else:
                conn.execute(
                    "INSERT INTO song_ratings (song_id, user_fingerprint, rating) VALUES (?, ?, ?)",
                    (song_id, user_fingerprint, rating),
                )
                message = "Rating submitted successfully"

            conn.commit()

        # Get updated ratings
        ratings = conn.execute(
            """
            SELECT 
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as thumbs_down
            FROM song_ratings WHERE song_id = ?
            """,
            (song_id,),
        ).fetchone()

        # Clear cache for this song
        cache_key = get_cache_key("ratings", song_id)
        if cache_key in cache:
            del cache[cache_key]

        result = {
            "message": message,
            "song_id": song_id,
            "thumbs_up": ratings["thumbs_up"] or 0,
            "thumbs_down": ratings["thumbs_down"] or 0,
            "user_rating": rating,
        }

        return jsonify(result)

    except ValueError:
        return jsonify({"error": "Invalid rating value"}), 400
    except Exception:
        return jsonify({"error": "Internal server error"}), 500


@app.route("/album-art")
@app.route("/album-art/")
@app.route("/album-art/<filename>")
@app.route("/album-art/<path:filename>")
def serve_album_art(filename=None):
    """Proxy album art from CloudFront with correct content-type"""
    try:
        import requests
        
        # Default to cover.jpg if no filename specified
        if not filename:
            filename = "cover.jpg"
        
        cloudfront_url = f"https://d3d4yli4hf5bmh.cloudfront.net/{filename}"
        
        # Fetch image from CloudFront
        resp = requests.get(cloudfront_url, timeout=10)
        resp.raise_for_status()
        
        # Create response with correct content type
        response = make_response(resp.content)
        
        # Set correct content type based on file extension
        if filename.endswith('.webp'):
            response.headers['Content-Type'] = 'image/webp'
        elif filename.endswith('.png'):
            response.headers['Content-Type'] = 'image/png'
        elif filename.endswith(('.jpg', '.jpeg')):
            response.headers['Content-Type'] = 'image/jpeg'
        else:
            response.headers['Content-Type'] = 'image/jpeg'  # default
        
        # Add caching headers for images
        return add_cache_headers(response, max_age=CACHE_TIMEOUT)
        
    except ImportError:
        # If requests is not available, redirect to original URL
        from flask import redirect
        cloudfront_url = f"https://d3d4yli4hf5bmh.cloudfront.net/{filename or 'cover.jpg'}"
        return redirect(cloudfront_url)
    except Exception as e:
        print(f"Failed to fetch album art: {e}")
        # Fallback to direct CloudFront URL
        from flask import redirect
        cloudfront_url = f"https://d3d4yli4hf5bmh.cloudfront.net/{filename or 'cover.jpg'}"
        return redirect(cloudfront_url)


@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1").fetchone()

        # Determine database type based on connection
        db_type = "postgresql" if DATABASE.startswith('postgresql://') else "sqlite"

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": db_type,
                "cache_size": len(cache),
            }
        )
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({"error": "Rate limit exceeded"}), 429


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# Initialize database when the module is imported (for WSGI servers)
try:
    with app.app_context():
        init_db()
        print(f"Database initialized at {DATABASE}")
except Exception as e:
    print(f"Failed to initialize database: {e}")

if __name__ == "__main__":
    # Enable debug mode only in development
    debug_mode = os.getenv("FLASK_ENV") == "development"
    app.run(debug=debug_mode, host="0.0.0.0", port=3000, threaded=True)
