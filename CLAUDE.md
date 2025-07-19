# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Radio Calico is a live streaming radio web application that serves high-quality lossless audio. The application consists of a Flask backend API and a frontend HTML/JavaScript player interface with real-time metadata and user rating functionality.

## Development Commands

### Running the Application
```bash
python app.py
```
- Starts Flask development server on `http://0.0.0.0:3000`
- Automatically initializes SQLite database
- Enables debug mode

### Dependencies
```bash
npm install    # Install Node.js dependencies (Express, CORS, SQLite3)
pip install flask flask-cors sqlite3  # Python dependencies
```

No build, test, or lint scripts are currently configured in package.json.

## Architecture Overview

### Backend (Flask/Python)
- **app.py**: Main Flask application with API endpoints
  - `/api/users` - User management (GET/POST)
  - `/api/ratings/<song_id>` - Song rating system (GET/POST)
  - Database initialization and SQLite operations
  - User fingerprinting for anonymous ratings

### Frontend Structure
- **index.html**: Main radio player interface
  - HLS.js integration for live audio streaming
  - Real-time metadata fetching from CloudFront
  - User rating system with thumbs up/down
  - Responsive design following brand guidelines

### Database Schema
- **users**: id, name, email, created_at
- **song_ratings**: id, song_id, user_fingerprint, rating (-1 or 1), created_at

### External Dependencies
- **Stream URL**: `https://d3d4yli4hf5bmh.cloudfront.net/hls/live.m3u8`
- **Metadata API**: `https://d3d4yli4hf5bmh.cloudfront.net/metadatav2.json`
- **Album Art**: `https://d3d4yli4hf5bmh.cloudfront.net/cover.jpg`
- **HLS.js**: CDN-loaded for audio streaming support

## Brand Guidelines

Colors defined in RadioCalico_Style_Guide.txt:
- **Mint**: #D8F2D5 (backgrounds, accents)
- **Forest Green**: #1F4E23 (buttons, headings)
- **Teal**: #38A29D (nav, hover states)
- **Calico Orange**: #EFA63C (highlights)
- **Charcoal**: #231F20 (text)

Typography: Montserrat (headings), Open Sans (body text)

## Key Implementation Details

### Audio Streaming
- Uses HLS.js for browser compatibility
- Fallback to native HLS for Safari
- Stream quality: 48kHz FLAC lossless
- Auto-retry on network errors

### Metadata System
- 10-second polling interval for live updates
- Handles current song and 5 previous tracks
- Dynamic album art refresh with cache-busting
- Song ID generation for rating persistence

### User Rating System
- Anonymous fingerprinting via User-Agent + IP hash
- Unique constraint prevents duplicate ratings per user/song
- Real-time vote count updates via AJAX

## File Structure Notes
- `static/` directory serves secondary assets
- `database.db` auto-created on first run
- Logo assets: RadioCalicoLogoTM.png, RadioCalicoLayout.png
- Style guide documentation in RadioCalico_Style_Guide.txt