const audio = document.getElementById('audioPlayer');
const playBtn = document.getElementById('playBtn');
const volumeSlider = document.getElementById('volumeSlider');
const status = document.getElementById('status');
const streamUrl = 'https://d3d4yli4hf5bmh.cloudfront.net/hls/live.m3u8';

// Debug: Check if elements are found
console.log('Elements found:');
console.log('- audio:', audio);
console.log('- playBtn:', playBtn);
console.log('- volumeSlider:', volumeSlider);
console.log('- status:', status);

let hls;

function updateStatus(message, className = '') {
    status.textContent = message;
    status.className = 'status ' + className;
}

function initializeHLS() {
    if (Hls.isSupported()) {
        hls = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
            backBufferLength: 90
        });

        hls.loadSource(streamUrl);
        hls.attachMedia(audio);

        hls.on(Hls.Events.MANIFEST_PARSED, function() {
            updateStatus('Stream loaded and ready', 'connecting');
        });

        hls.on(Hls.Events.ERROR, function(event, data) {
            console.error('HLS Error:', data);
            if (data.fatal) {
                switch(data.type) {
                    case Hls.ErrorTypes.NETWORK_ERROR:
                        updateStatus('Network error - retrying...', 'error');
                        hls.startLoad();
                        break;
                    case Hls.ErrorTypes.MEDIA_ERROR:
                        updateStatus('Media error - recovering...', 'error');
                        hls.recoverMediaError();
                        break;
                    default:
                        updateStatus('Fatal error occurred', 'error');
                        hls.destroy();
                        break;
                }
            }
        });

    } else if (audio.canPlayType('application/vnd.apple.mpegurl')) {
        audio.src = streamUrl;
        updateStatus('Using native HLS support', 'connecting');
    } else {
        updateStatus('HLS not supported in this browser', 'error');
    }
}

volumeSlider.addEventListener('input', function() {
    audio.volume = this.value;
});

audio.addEventListener('loadstart', () => updateStatus('Loading stream...', 'connecting'));
audio.addEventListener('canplay', () => updateStatus('Stream ready to play', 'connecting'));
audio.addEventListener('playing', () => updateStatus('Playing live stream', 'playing'));
audio.addEventListener('pause', () => updateStatus('Stream paused', ''));
audio.addEventListener('ended', () => updateStatus('Stream ended', ''));
audio.addEventListener('error', () => updateStatus('Stream error occurred', 'error'));

audio.volume = 0.7;

// Metadata functionality
const metadataUrl = 'https://d3d4yli4hf5bmh.cloudfront.net/metadatav2.json';
let metadataUpdateInterval;
let currentSongId = null;

async function fetchMetadata() {
    try {
        console.log('Fetching metadata from:', metadataUrl);
        const response = await fetch(metadataUrl);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Metadata received:', data);
        
        updateNowPlaying(data);
        updateRecentlyPlayed(parsePreviousTracks(data));
        updateStreamQuality(data);
    } catch (error) {
        console.error('Failed to fetch metadata:', error);
        updateStatus('Metadata unavailable - ' + error.message, 'error');
        
        // Set fallback data for testing
        updateNowPlaying({
            title: 'Test Song',
            artist: 'Test Artist', 
            album: 'Test Album',
            releaseDate: '2023'
        });
        
        // Set fallback quality info
        updateStreamQuality({
            bitDepth: '16',
            sampleRate: '44100',
            format: 'FLAC'
        });
    }
}

function parsePreviousTracks(data) {
    const tracks = [];
    for (let i = 1; i <= 5; i++) {
        const artist = data[`prev_artist_${i}`];
        const title = data[`prev_title_${i}`];
        if (artist && title) {
            tracks.push({
                artist: artist,
                title: title,
                album: data[`prev_album_${i}`] || ''
            });
        }
    }
    return tracks;
}

function updateNowPlaying(data) {
    console.log('Updating now playing with data:', data);
    
    document.getElementById('currentTitle').textContent = data.title || 'Unknown Title';
    document.getElementById('currentArtist').textContent = data.artist || 'Unknown Artist';
    document.getElementById('currentAlbum').textContent = data.album || 'Unknown Album';
    
    // Update year banner
    const yearBanner = document.getElementById('yearBanner');
    console.log('Release date from data:', data.releaseDate);
    
    if (data.releaseDate) {
        yearBanner.textContent = data.releaseDate;
        yearBanner.style.display = 'block';
        console.log('Year banner updated to:', data.releaseDate);
    } else {
        // Try alternative field names
        const year = data.year || data.release_year || data.release_date;
        console.log('Trying alternative year fields:', year);
        
        if (year) {
            yearBanner.textContent = year;
            yearBanner.style.display = 'block';
            console.log('Year banner updated with alternative field:', year);
        } else {
            yearBanner.style.display = 'none';
            console.log('No year information found, hiding banner');
        }
    }
    
    // Force refresh album art by adding timestamp
    const albumArt = document.getElementById('albumArt');
    const timestamp = new Date().getTime();
    albumArt.src = `https://d3d4yli4hf5bmh.cloudfront.net/cover.jpg?t=${timestamp}`;
    
    // Generate song ID and load ratings
    const newSongId = generateSongId(data);
    if (newSongId !== currentSongId) {
        currentSongId = newSongId;
        loadRatings(currentSongId);
    }
}

function generateSongId(data) {
    const artist = data.artist || 'Unknown';
    const title = data.title || 'Unknown';
    return btoa(`${artist}-${title}`).replace(/[^a-zA-Z0-9]/g, '');
}

function updateRecentlyPlayed(tracks) {
    const recentTracksContainer = document.getElementById('recentTracks');
    recentTracksContainer.innerHTML = '';
    
    tracks.slice(0, 5).forEach(track => {
        const trackElement = document.createElement('div');
        trackElement.className = 'track-item';
        trackElement.innerHTML = `
            <span class="track-artist-name">${track.artist || 'Unknown Artist'}:</span>
            <span class="track-song-name">${track.title || 'Unknown Title'}</span>
        `;
        recentTracksContainer.appendChild(trackElement);
    });
}

function updateStreamQuality(data) {
    // Update source quality from metadata
    const sourceBitDepth = data.bitDepth || data.bit_depth || '24';
    const sourceSampleRate = data.sampleRate || data.sample_rate || '96000';
    const sourceFormat = data.format || 'FLAC';
    const sourceQualityText = `Source quality: ${sourceBitDepth}-bit ${(sourceSampleRate / 1000).toFixed(1)}kHz ${sourceFormat}`;
    document.getElementById('sourceQuality').textContent = sourceQualityText;
    
    // Update stream quality (this could be different from source if transcoded)
    const streamSampleRate = data.streamSampleRate || data.stream_sample_rate || sourceSampleRate;
    const streamFormat = data.streamFormat || data.stream_format || 'FLAC';
    const streamQualityText = `Stream quality: ${(streamSampleRate / 1000).toFixed(0)}kHz ${streamFormat} / HLS Lossless`;
    document.getElementById('streamQuality').textContent = streamQualityText;
}

function startMetadataUpdates() {
    fetchMetadata();
    metadataUpdateInterval = setInterval(fetchMetadata, 10000);
}

function stopMetadataUpdates() {
    if (metadataUpdateInterval) {
        clearInterval(metadataUpdateInterval);
        metadataUpdateInterval = null;
    }
}

// Update play button to also start metadata updates
playBtn.addEventListener('click', function() {
    console.log('Play button clicked! Audio paused:', audio.paused);
    
    if (audio.paused) {
        if (!hls && !audio.src) {
            console.log('Initializing HLS...');
            initializeHLS();
        }
        
        updateStatus('Connecting to stream...', 'connecting');
        console.log('Attempting to play audio...');
        audio.play().then(() => {
            console.log('Audio started playing successfully');
            updateStatus('Playing live stream', 'playing');
            playBtn.textContent = '⏸️';
            startMetadataUpdates();
        }).catch(error => {
            console.error('Playback failed:', error);
            updateStatus('Playback failed - try again', 'error');
        });
    } else {
        console.log('Pausing audio...');
        audio.pause();
        updateStatus('Stream paused', '');
        playBtn.textContent = '▶️';
        stopMetadataUpdates();
    }
});

// Rating functionality
async function loadRatings(songId) {
    try {
        const response = await fetch(`/api/ratings/${songId}`);
        const data = await response.json();
        updateRatingDisplay(data);
    } catch (error) {
        console.error('Failed to load ratings:', error);
    }
}

async function submitRating(songId, rating) {
    try {
        const response = await fetch(`/api/ratings/${songId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ rating: rating })
        });
        const data = await response.json();
        updateRatingDisplay(data);
        
        if (response.ok) {
            document.getElementById('ratingStats').textContent = data.message;
        } else {
            document.getElementById('ratingStats').textContent = data.error || 'Rating failed';
        }
    } catch (error) {
        console.error('Failed to submit rating:', error);
        document.getElementById('ratingStats').textContent = 'Rating failed';
    }
}

function updateRatingDisplay(data) {
    document.getElementById('thumbsUpCount').textContent = data.thumbs_up || 0;
    document.getElementById('thumbsDownCount').textContent = data.thumbs_down || 0;
    
    const thumbsUpBtn = document.getElementById('thumbsUpBtn');
    const thumbsDownBtn = document.getElementById('thumbsDownBtn');
    
    // Reset button states
    thumbsUpBtn.classList.remove('active-up');
    thumbsDownBtn.classList.remove('active-down');
    
    // Highlight user's current rating
    if (data.user_rating === 1) {
        thumbsUpBtn.classList.add('active-up');
    } else if (data.user_rating === -1) {
        thumbsDownBtn.classList.add('active-down');
    }
    
    const total = (data.thumbs_up || 0) + (data.thumbs_down || 0);
    if (total > 0) {
        document.getElementById('ratingStats').textContent = `${total} listener${total === 1 ? '' : 's'} rated this song`;
    }
}

// Event listeners for rating buttons
document.getElementById('thumbsUpBtn').addEventListener('click', function() {
    if (currentSongId) {
        submitRating(currentSongId, 1);
    }
});

document.getElementById('thumbsDownBtn').addEventListener('click', function() {
    if (currentSongId) {
        submitRating(currentSongId, -1);
    }
});

// Load initial metadata on page load
fetchMetadata();