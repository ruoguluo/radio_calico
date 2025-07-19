# Radio Calico 🎵

A high-quality live streaming radio application featuring lossless audio, real-time metadata, and community-driven song ratings.

![Radio Calico Logo](static/RadioCalicoLogoTM.png)

## Features

- **🎧 Lossless Audio Streaming**: High-quality FLAC streaming via HLS (HTTP Live Streaming)
- **📊 Real-time Metadata**: Live track information with album art and release years
- **👍 Community Ratings**: Thumbs up/down rating system for tracks
- **📱 Responsive Design**: Modern, mobile-friendly interface
- **🔊 Audio Controls**: Volume control and playback management
- **📜 Recent Tracks**: Display of previously played songs
- **🌐 Cross-Platform**: Works across modern web browsers

## Technology Stack

### Backend
- **Python Flask**: REST API server
- **SQLite**: Database for user data and song ratings
- **Flask-CORS**: Cross-origin resource sharing support

### Frontend
- **HTML5 Audio**: Native audio playback with HLS.js fallback
- **HLS.js**: HTTP Live Streaming support for browsers
- **Vanilla JavaScript**: No framework dependencies
- **CSS3**: Custom styling with brand colors

### Infrastructure
- **CloudFront CDN**: Audio streaming and metadata delivery
- **AWS S3**: Static asset hosting

## Quick Start

### Prerequisites
- Python 3.7+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ruoguluo/radio_calico.git
   cd radio_calico
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:3000`

## API Endpoints

### Users
- `GET /api/users` - Get all registered users
- `POST /api/users` - Create a new user
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com"
  }
  ```

### Song Ratings
- `GET /api/ratings/<song_id>` - Get rating statistics for a song
- `POST /api/ratings/<song_id>` - Submit a rating (1 for thumbs up, -1 for thumbs down)
  ```json
  {
    "rating": 1
  }
  ```

## Project Structure

```
radio-calico/
├── app.py                      # Flask backend server
├── test_app.py                 # Comprehensive test suite
├── run_tests.py                # Test runner script
├── requirements.txt            # Python dependencies
├── index.html                  # Main application interface
├── database.db                 # SQLite database
├── stream_URL.txt             # Streaming endpoint URL
├── static/                    # Frontend assets
│   ├── script.js              # JavaScript functionality
│   ├── styles.css             # CSS styling
│   ├── index.html             # Alternative interface
│   └── RadioCalicoLogoTM.png  # Logo assets
├── RadioCalicoLayout.png       # Design mockups
├── RadioCalicoLogoTM.png       # Main logo
├── RadioCalicoStyle.zip        # Style assets
├── RadioCalico_Style_Guide.txt # Brand guidelines
└── CLAUDE.md                   # Development notes
```

## Configuration

### Stream Configuration
The application streams from: `https://d3d4yli4hf5bmh.cloudfront.net/hls/live.m3u8`

### Metadata Source
Real-time metadata is fetched from: `https://d3d4yli4hf5bmh.cloudfront.net/metadatav2.json`

### Database Schema
```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Song ratings table
CREATE TABLE song_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id TEXT NOT NULL,
    user_fingerprint TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK(rating IN (1, -1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(song_id, user_fingerprint)
);
```

## Brand Guidelines

Radio Calico follows a distinctive brand identity:

### Colors
- **Mint**: `#D8F2D5` - Background accents
- **Forest Green**: `#1F4E23` - Primary buttons and headings
- **Teal**: `#38A29D` - Navigation and highlights
- **Calico Orange**: `#EFA63C` - Call-to-action elements
- **Charcoal**: `#231F20` - Body text

### Typography
- **Headings**: Montserrat (500-700 weight)
- **Body**: Open Sans (400 weight)

## Development

### Running in Development Mode
```bash
python app.py
```
The server runs on `http://localhost:3000` with debug mode enabled.

### Running Tests
The project includes comprehensive tests for all API endpoints and functionality.

```bash
# Run all tests
python test_app.py

# Or use the test runner for detailed output
python run_tests.py

# Run specific test methods
python -m unittest test_app.RadioCalicoTestCase.test_create_user_success
```

**Test Coverage:**
- API endpoint testing (users, ratings)
- Database operations and constraints
- User fingerprinting functionality
- Error handling and validation
- Static file serving

### Database Initialization
The database is automatically initialized when the application starts. Tables are created if they don't exist.

### User Fingerprinting
The application uses a combination of User-Agent and IP address to create anonymous user fingerprints for rating functionality, ensuring users can only rate each song once.

## Features in Detail

### Audio Streaming
- Utilizes HLS (HTTP Live Streaming) for adaptive bitrate streaming
- Falls back to native browser HLS support on Safari
- Supports FLAC lossless audio quality
- Real-time stream status monitoring

### Rating System
- Anonymous voting using browser fingerprinting
- Prevents multiple votes from the same user
- Real-time rating updates
- Persistent storage in SQLite database

### Metadata Integration
- Fetches current track information every 10 seconds
- Displays artist, title, album, and release year
- Updates album artwork dynamically
- Shows recently played tracks history

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the ISC License.

## Support

For support, please open an issue on GitHub or contact the development team.

---

**Radio Calico** - *Crystal clear audio, community driven* 🎵
