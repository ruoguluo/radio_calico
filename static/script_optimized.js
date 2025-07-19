// Optimized Radio Russell JavaScript
// Use requestIdleCallback for non-critical operations
const scheduleWork = window.requestIdleCallback || ((cb) => setTimeout(cb, 16));

// Cache DOM elements to avoid repeated queries
const elements = {
    audio: document.getElementById('audioPlayer'),
    playBtn: document.getElementById('playBtn'),
    volumeSlider: document.getElementById('volumeSlider'),
    status: document.getElementById('status'),
    currentTitle: document.getElementById('currentTitle'),
    currentArtist: document.getElementById('currentArtist'),
    currentAlbum: document.getElementById('currentAlbum'),
    yearBanner: document.getElementById('yearBanner'),
    albumArt: document.getElementById('albumArt'),
    sourceQuality: document.getElementById('sourceQuality'),
    streamQuality: document.getElementById('streamQuality'),
    thumbsUpBtn: document.getElementById('thumbsUpBtn'),
    thumbsDownBtn: document.getElementById('thumbsDownBtn'),
    thumbsUpCount: document.getElementById('thumbsUpCount'),
    thumbsDownCount: document.getElementById('thumbsDownCount'),
    ratingStats: document.getElementById('ratingStats'),
    recentTracks: document.getElementById('recentTracks')
};

// Configuration
const config = {
    streamUrl: 'https://d3d4yli4hf5bmh.cloudfront.net/hls/live.m3u8',
    metadataUrl: 'https://d3d4yli4hf5bmh.cloudfront.net/metadatav2.json',
    metadataInterval: 10000, // 10 seconds
    retryDelay: 5000 // 5 seconds
};

// State management
const state = {
    hls: null,
    metadataUpdateInterval: null,
    currentSongId: null,
    isPlaying: false,
    lastMetadataFetch: 0,
    metadataCache: new Map()
};

// Utility functions
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

const throttle = (func, limit) => {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
};

// Status update with minimal DOM manipulation
function updateStatus(message, className = '') {
    elements.status.textContent = message;
    elements.status.className = `status ${className}`;
}

// Optimized HLS initialization with error handling
function initializeHLS() {
    return new Promise((resolve, reject) => {
        if (!window.Hls) {
            reject(new Error('HLS.js not loaded'));
            return;
        }

        if (Hls.isSupported()) {
            state.hls = new Hls({
                enableWorker: true,
                lowLatencyMode: true,
                backBufferLength: 90,
                maxBufferLength: 30,
                maxMaxBufferLength: 600
            });

            state.hls.loadSource(config.streamUrl);
            state.hls.attachMedia(elements.audio);

            state.hls.on(Hls.Events.MANIFEST_PARSED, () => {
                updateStatus('Stream loaded and ready', 'connecting');
                resolve();
            });

            state.hls.on(Hls.Events.ERROR, (event, data) => {
                console.warn('HLS Error:', data);
                if (data.fatal) {
                    handleHLSError(data);
                }
            });

        } else if (elements.audio.canPlayType('application/vnd.apple.mpegurl')) {
            elements.audio.src = config.streamUrl;
            updateStatus('Using native HLS support', 'connecting');
            resolve();
        } else {
            reject(new Error('HLS not supported in this browser'));
        }
    });
}

function handleHLSError(data) {
    switch(data.type) {
        case Hls.ErrorTypes.NETWORK_ERROR:
            updateStatus('Network error - retrying...', 'error');
            scheduleWork(() => state.hls.startLoad());
            break;
        case Hls.ErrorTypes.MEDIA_ERROR:
            updateStatus('Media error - recovering...', 'error');
            scheduleWork(() => state.hls.recoverMediaError());
            break;
        default:
            updateStatus('Fatal error occurred', 'error');
            state.hls.destroy();
            state.hls = null;
            break;
    }
}

// Optimized metadata fetching with caching and deduplication
async function fetchMetadata() {
    const now = Date.now();
    
    // Prevent duplicate requests
    if (now - state.lastMetadataFetch < 1000) {
        return;
    }
    
    state.lastMetadataFetch = now;

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
        
        const response = await fetch(config.metadataUrl, {
            signal: controller.signal,
            cache: 'no-cache'
        });
        
        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        
        // Cache the metadata briefly to avoid redundant processing
        const cacheKey = JSON.stringify(data);
        if (state.metadataCache.has(cacheKey)) {
            return;
        }
        
        state.metadataCache.set(cacheKey, data);
        // Clear old cache entries (keep only last 3)
        if (state.metadataCache.size > 3) {
            const firstKey = state.metadataCache.keys().next().value;
            state.metadataCache.delete(firstKey);
        }

        // Process metadata in idle callback
        scheduleWork(() => {
            updateNowPlaying(data);
            updateRecentlyPlayed(parsePreviousTracks(data));
            updateStreamQuality(data);
        });

    } catch (error) {
        console.warn('Metadata fetch failed:', error);
        if (error.name !== 'AbortError') {
            updateStatus(`Metadata unavailable`, 'error');
        }
    }
}

// Optimized DOM updates with DocumentFragment for multiple elements
function updateRecentlyPlayed(tracks) {
    const fragment = document.createDocumentFragment();
    
    tracks.slice(0, 5).forEach(track => {
        const trackElement = document.createElement('div');
        trackElement.className = 'track-item';
        
        const artistSpan = document.createElement('span');
        artistSpan.className = 'track-artist-name';
        artistSpan.textContent = `${track.artist || 'Unknown Artist'}:`;
        
        const titleSpan = document.createElement('span');
        titleSpan.className = 'track-song-name';
        titleSpan.textContent = track.title || 'Unknown Title';
        
        trackElement.appendChild(artistSpan);
        trackElement.appendChild(titleSpan);
        fragment.appendChild(trackElement);
    });
    
    elements.recentTracks.innerHTML = '';
    elements.recentTracks.appendChild(fragment);
}

function updateNowPlaying(data) {
    // Batch DOM updates
    elements.currentTitle.textContent = data.title || 'Unknown Title';
    elements.currentArtist.textContent = data.artist || 'Unknown Artist';
    elements.currentAlbum.textContent = data.album || 'Unknown Album';
    
    // Update year banner
    const year = data.releaseDate || data.year || data.release_year || data.release_date;
    if (year) {
        elements.yearBanner.textContent = year;
        elements.yearBanner.style.display = 'block';
    } else {
        elements.yearBanner.style.display = 'none';
    }
    
    // Optimize album art loading with timestamp
    const timestamp = Date.now();
    elements.albumArt.src = `https://d3d4yli4hf5bmh.cloudfront.net/cover.jpg?t=${timestamp}`;
    
    // Handle song change for ratings
    const newSongId = generateSongId(data);
    if (newSongId !== state.currentSongId) {
        state.currentSongId = newSongId;
        // Load ratings in idle callback to avoid blocking
        scheduleWork(() => loadRatings(state.currentSongId));
    }
}

function parsePreviousTracks(data) {
    const tracks = [];
    for (let i = 1; i <= 5; i++) {
        const artist = data[`prev_artist_${i}`];
        const title = data[`prev_title_${i}`];
        if (artist && title) {
            tracks.push({
                artist,
                title,
                album: data[`prev_album_${i}`] || ''
            });
        }
    }
    return tracks;
}

function generateSongId(data) {
    const artist = data.artist || 'Unknown';
    const title = data.title || 'Unknown';
    return btoa(`${artist}-${title}`).replace(/[^a-zA-Z0-9]/g, '');
}

function updateStreamQuality(data) {
    const sourceBitDepth = data.bitDepth || data.bit_depth || '24';
    const sourceSampleRate = data.sampleRate || data.sample_rate || '96000';
    const sourceFormat = data.format || 'FLAC';
    
    elements.sourceQuality.textContent = `Source: ${sourceBitDepth}-bit ${(sourceSampleRate / 1000).toFixed(1)}kHz ${sourceFormat}`;
    
    const streamSampleRate = data.streamSampleRate || data.stream_sample_rate || sourceSampleRate;
    const streamFormat = data.streamFormat || data.stream_format || 'FLAC';
    elements.streamQuality.textContent = `Stream: ${(streamSampleRate / 1000).toFixed(0)}kHz ${streamFormat} / HLS`;
}

// Optimized rating system with request deduplication
const ratingRequests = new Map();

async function loadRatings(songId) {
    if (ratingRequests.has(`load-${songId}`)) {
        return ratingRequests.get(`load-${songId}`);
    }

    const promise = fetch(`/api/ratings/${songId}`)
        .then(response => response.json())
        .then(data => {
            updateRatingDisplay(data);
            return data;
        })
        .catch(error => {
            console.warn('Failed to load ratings:', error);
        })
        .finally(() => {
            ratingRequests.delete(`load-${songId}`);
        });

    ratingRequests.set(`load-${songId}`, promise);
    return promise;
}

const submitRating = throttle(async (songId, rating) => {
    const key = `submit-${songId}-${rating}`;
    if (ratingRequests.has(key)) {
        return;
    }

    const promise = fetch(`/api/ratings/${songId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating })
    })
    .then(response => response.json())
    .then(data => {
        updateRatingDisplay(data);
        elements.ratingStats.textContent = data.message || (response.ok ? 'Rating submitted' : 'Rating failed');
    })
    .catch(error => {
        console.warn('Failed to submit rating:', error);
        elements.ratingStats.textContent = 'Rating failed';
    })
    .finally(() => {
        ratingRequests.delete(key);
    });

    ratingRequests.set(key, promise);
}, 1000); // Throttle to prevent spam

function updateRatingDisplay(data) {
    elements.thumbsUpCount.textContent = data.thumbs_up || 0;
    elements.thumbsDownCount.textContent = data.thumbs_down || 0;
    
    // Update button states
    elements.thumbsUpBtn.classList.toggle('active-up', data.user_rating === 1);
    elements.thumbsDownBtn.classList.toggle('active-down', data.user_rating === -1);
    
    const total = (data.thumbs_up || 0) + (data.thumbs_down || 0);
    if (total > 0) {
        elements.ratingStats.textContent = `${total} listener${total === 1 ? '' : 's'} rated this song`;
    }
}

// Event handlers with better error handling
const handlePlayPause = async () => {
    try {
        if (elements.audio.paused) {
            if (!state.hls && !elements.audio.src) {
                updateStatus('Initializing stream...', 'connecting');
                await initializeHLS();
            }
            
            updateStatus('Connecting...', 'connecting');
            await elements.audio.play();
            
            elements.playBtn.textContent = '⏸️';
            state.isPlaying = true;
            startMetadataUpdates();
            updateStatus('Playing live stream', 'playing');
            
        } else {
            elements.audio.pause();
            elements.playBtn.textContent = '▶️';
            state.isPlaying = false;
            stopMetadataUpdates();
            updateStatus('Stream paused', '');
        }
    } catch (error) {
        console.error('Playback failed:', error);
        updateStatus('Playback failed - try again', 'error');
    }
};

function startMetadataUpdates() {
    fetchMetadata(); // Immediate fetch
    state.metadataUpdateInterval = setInterval(fetchMetadata, config.metadataInterval);
}

function stopMetadataUpdates() {
    if (state.metadataUpdateInterval) {
        clearInterval(state.metadataUpdateInterval);
        state.metadataUpdateInterval = null;
    }
}

// Initialize event listeners with passive events where appropriate
function initializeEventListeners() {
    // Throttled volume control
    elements.volumeSlider.addEventListener('input', throttle(() => {
        elements.audio.volume = elements.volumeSlider.value;
    }, 50), { passive: true });

    // Audio event listeners
    elements.audio.addEventListener('loadstart', () => updateStatus('Loading...', 'connecting'), { passive: true });
    elements.audio.addEventListener('canplay', () => updateStatus('Ready to play', 'connecting'), { passive: true });
    elements.audio.addEventListener('playing', () => updateStatus('Playing', 'playing'), { passive: true });
    elements.audio.addEventListener('pause', () => updateStatus('Paused', ''), { passive: true });
    elements.audio.addEventListener('error', () => updateStatus('Stream error', 'error'), { passive: true });

    // Play button
    elements.playBtn.addEventListener('click', handlePlayPause);

    // Rating buttons
    elements.thumbsUpBtn.addEventListener('click', () => {
        if (state.currentSongId) submitRating(state.currentSongId, 1);
    });

    elements.thumbsDownBtn.addEventListener('click', () => {
        if (state.currentSongId) submitRating(state.currentSongId, -1);
    });

    // Set initial volume
    elements.audio.volume = 0.7;
}

// Intersection Observer for lazy loading (if needed in the future)
const observerOptions = {
    root: null,
    rootMargin: '50px',
    threshold: 0.1
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEventListeners);
} else {
    initializeEventListeners();
}

// Load initial metadata
scheduleWork(() => {
    fetchMetadata();
});
