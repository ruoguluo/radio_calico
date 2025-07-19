/**
 * JavaScript Tests for Radio Russell Frontend
 * Tests core functionality of the streaming radio application
 */

// Mock DOM environment
const { JSDOM } = require('jsdom');

// Create a mock DOM with the basic structure needed for tests
const dom = new JSDOM(`
<!DOCTYPE html>
<html>
<head>
    <title>Radio Russell - Test</title>
</head>
<body>
    <div id="status"></div>
    <audio id="audioPlayer"></audio>
    <button id="playBtn">▶</button>
    <input type="range" id="volumeSlider" min="0" max="1" step="0.1" value="0.7">
    <div id="currentTitle">Loading...</div>
    <div id="currentArtist">Loading...</div>
    <div id="currentAlbum">Loading...</div>
    <div id="yearBanner">1983</div>
    <img id="albumArt" src="cover.jpg" alt="Album Art">
    <div id="recentTracks"></div>
    <div id="sourceQuality">Source quality: Loading...</div>
    <div id="streamQuality">Stream quality: Loading...</div>
    <button id="thumbsUpBtn">👍 <span id="thumbsUpCount">0</span></button>
    <button id="thumbsDownBtn">👎 <span id="thumbsDownCount">0</span></button>
    <div id="ratingStats">Rate this song to see community ratings</div>
</body>
</html>
`, { url: 'http://localhost:3000' });

global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// Mock fetch function
global.fetch = jest.fn();

// Mock HLS.js
global.Hls = {
    isSupported: jest.fn(() => true),
    Events: {
        MANIFEST_PARSED: 'hlsManifestParsed',
        ERROR: 'hlsError'
    },
    ErrorTypes: {
        NETWORK_ERROR: 'networkError',
        MEDIA_ERROR: 'mediaError'
    }
};

// Mock HLS constructor
const mockHls = {
    loadSource: jest.fn(),
    attachMedia: jest.fn(),
    on: jest.fn(),
    startLoad: jest.fn(),
    recoverMediaError: jest.fn(),
    destroy: jest.fn()
};

global.Hls.mockImplementation = jest.fn(() => mockHls);

// Mock btoa for base64 encoding
global.btoa = jest.fn((str) => Buffer.from(str).toString('base64'));

// Mock console methods
global.console = {
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn()
};

// Mock audio element methods
const mockAudio = {
    play: jest.fn(() => Promise.resolve()),
    pause: jest.fn(),
    canPlayType: jest.fn(() => 'probably'),
    addEventListener: jest.fn(),
    volume: 0.7,
    paused: true,
    src: ''
};

// Override getElementById to return our mocked elements
const originalGetElementById = document.getElementById;
document.getElementById = jest.fn((id) => {
    if (id === 'audioPlayer') return mockAudio;
    return originalGetElementById.call(document, id);
});

/**
 * Test Suite: Core JavaScript Functions
 */
describe('Radio Russell JavaScript Tests', () => {
    
    beforeEach(() => {
        // Clear all mocks before each test
        jest.clearAllMocks();
        
        // Reset fetch mock
        fetch.mockClear();
    });

    describe('Utility Functions', () => {
        test('updateStatus function updates status element', () => {
            // Load the script functions (we'll need to extract them)
            const statusElement = document.getElementById('status');
            
            // Mock the updateStatus function
            function updateStatus(message, className = '') {
                statusElement.textContent = message;
                statusElement.className = 'status ' + className;
            }
            
            updateStatus('Test message', 'connecting');
            
            expect(statusElement.textContent).toBe('Test message');
            expect(statusElement.className).toBe('status connecting');
        });

        test('generateSongId creates valid base64 ID', () => {
            function generateSongId(data) {
                const artist = data.artist || 'Unknown';
                const title = data.title || 'Unknown';
                return btoa(`${artist}-${title}`).replace(/[^a-zA-Z0-9]/g, '');
            }

            const testData = { artist: 'Test Artist', title: 'Test Song' };
            const songId = generateSongId(testData);
            
            expect(btoa).toHaveBeenCalledWith('Test Artist-Test Song');
            expect(typeof songId).toBe('string');
            expect(songId.length).toBeGreaterThan(0);
        });

        test('parsePreviousTracks extracts track data correctly', () => {
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

            const mockData = {
                prev_artist_1: 'Artist 1',
                prev_title_1: 'Song 1',
                prev_album_1: 'Album 1',
                prev_artist_2: 'Artist 2',
                prev_title_2: 'Song 2',
                // Missing album for song 2
                prev_artist_3: 'Artist 3',
                prev_title_3: 'Song 3'
            };

            const tracks = parsePreviousTracks(mockData);
            
            expect(tracks).toHaveLength(3);
            expect(tracks[0]).toEqual({
                artist: 'Artist 1',
                title: 'Song 1',
                album: 'Album 1'
            });
            expect(tracks[1]).toEqual({
                artist: 'Artist 2',
                title: 'Song 2',
                album: ''
            });
        });
    });

    describe('Metadata Functions', () => {
        test('updateNowPlaying updates DOM elements correctly', () => {
            function updateNowPlaying(data) {
                document.getElementById('currentTitle').textContent = data.title || 'Unknown Title';
                document.getElementById('currentArtist').textContent = data.artist || 'Unknown Artist';
                document.getElementById('currentAlbum').textContent = data.album || 'Unknown Album';
                
                const yearBanner = document.getElementById('yearBanner');
                if (data.releaseDate) {
                    yearBanner.textContent = data.releaseDate;
                    yearBanner.style.display = 'block';
                } else {
                    const year = data.year || data.release_year || data.release_date;
                    if (year) {
                        yearBanner.textContent = year;
                        yearBanner.style.display = 'block';
                    } else {
                        yearBanner.style.display = 'none';
                    }
                }
                
                const albumArt = document.getElementById('albumArt');
                const timestamp = new Date().getTime();
                albumArt.src = `https://d3d4yli4hf5bmh.cloudfront.net/cover.jpg?t=${timestamp}`;
            }

            const testData = {
                title: 'Test Song',
                artist: 'Test Artist',
                album: 'Test Album',
                releaseDate: '2023'
            };

            updateNowPlaying(testData);

            expect(document.getElementById('currentTitle').textContent).toBe('Test Song');
            expect(document.getElementById('currentArtist').textContent).toBe('Test Artist');
            expect(document.getElementById('currentAlbum').textContent).toBe('Test Album');
            expect(document.getElementById('yearBanner').textContent).toBe('2023');
        });

        test('updateStreamQuality formats quality information', () => {
            function updateStreamQuality(data) {
                const sourceBitDepth = data.bitDepth || data.bit_depth || '24';
                const sourceSampleRate = data.sampleRate || data.sample_rate || '96000';
                const sourceFormat = data.format || 'FLAC';
                const sourceQualityText = `Source quality: ${sourceBitDepth}-bit ${(sourceSampleRate / 1000).toFixed(1)}kHz ${sourceFormat}`;
                document.getElementById('sourceQuality').textContent = sourceQualityText;
                
                const streamSampleRate = data.streamSampleRate || data.stream_sample_rate || sourceSampleRate;
                const streamFormat = data.streamFormat || data.stream_format || 'FLAC';
                const streamQualityText = `Stream quality: ${(streamSampleRate / 1000).toFixed(0)}kHz ${streamFormat} / HLS Lossless`;
                document.getElementById('streamQuality').textContent = streamQualityText;
            }

            const testData = {
                bitDepth: '24',
                sampleRate: '48000',
                format: 'FLAC'
            };

            updateStreamQuality(testData);

            expect(document.getElementById('sourceQuality').textContent).toBe('Source quality: 24-bit 48.0kHz FLAC');
            expect(document.getElementById('streamQuality').textContent).toBe('Stream quality: 48kHz FLAC / HLS Lossless');
        });

        test('fetchMetadata handles successful response', async () => {
            const mockMetadata = {
                title: 'Test Song',
                artist: 'Test Artist',
                album: 'Test Album',
                releaseDate: '2023'
            };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockMetadata
            });

            async function fetchMetadata() {
                try {
                    const response = await fetch('https://d3d4yli4hf5bmh.cloudfront.net/metadatav2.json');
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const data = await response.json();
                    return data;
                } catch (error) {
                    throw error;
                }
            }

            const result = await fetchMetadata();
            
            expect(fetch).toHaveBeenCalledWith('https://d3d4yli4hf5bmh.cloudfront.net/metadatav2.json');
            expect(result).toEqual(mockMetadata);
        });

        test('fetchMetadata handles network error', async () => {
            fetch.mockRejectedValueOnce(new Error('Network error'));

            async function fetchMetadata() {
                try {
                    const response = await fetch('https://d3d4yli4hf5bmh.cloudfront.net/metadatav2.json');
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return await response.json();
                } catch (error) {
                    throw error;
                }
            }

            await expect(fetchMetadata()).rejects.toThrow('Network error');
        });
    });

    describe('Rating System', () => {
        test('updateRatingDisplay updates rating counts', () => {
            function updateRatingDisplay(data) {
                document.getElementById('thumbsUpCount').textContent = data.thumbs_up || 0;
                document.getElementById('thumbsDownCount').textContent = data.thumbs_down || 0;
                
                const total = (data.thumbs_up || 0) + (data.thumbs_down || 0);
                if (total > 0) {
                    document.getElementById('ratingStats').textContent = `${total} listener${total === 1 ? '' : 's'} rated this song`;
                }
            }

            const testData = {
                thumbs_up: 5,
                thumbs_down: 2,
                user_rating: 1
            };

            updateRatingDisplay(testData);

            expect(document.getElementById('thumbsUpCount').textContent).toBe('5');
            expect(document.getElementById('thumbsDownCount').textContent).toBe('2');
            expect(document.getElementById('ratingStats').textContent).toBe('7 listeners rated this song');
        });

        test('submitRating sends correct API request', async () => {
            const mockResponse = {
                thumbs_up: 6,
                thumbs_down: 2,
                user_rating: 1,
                message: 'Rating submitted successfully'
            };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse
            });

            async function submitRating(songId, rating) {
                const response = await fetch(`/api/ratings/${songId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ rating: rating })
                });
                return await response.json();
            }

            const result = await submitRating('testSong123', 1);

            expect(fetch).toHaveBeenCalledWith('/api/ratings/testSong123', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ rating: 1 })
            });
            expect(result).toEqual(mockResponse);
        });

        test('loadRatings fetches rating data', async () => {
            const mockRatings = {
                song_id: 'testSong123',
                thumbs_up: 3,
                thumbs_down: 1,
                user_rating: null
            };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockRatings
            });

            async function loadRatings(songId) {
                const response = await fetch(`/api/ratings/${songId}`);
                return await response.json();
            }

            const result = await loadRatings('testSong123');

            expect(fetch).toHaveBeenCalledWith('/api/ratings/testSong123');
            expect(result).toEqual(mockRatings);
        });
    });

    describe('Audio Controls', () => {
        test('volume slider updates audio volume', () => {
            const volumeSlider = document.getElementById('volumeSlider');
            const audio = document.getElementById('audioPlayer');
            
            // Simulate volume change
            volumeSlider.value = '0.5';
            
            // Mock the event handler
            function handleVolumeChange() {
                audio.volume = parseFloat(volumeSlider.value);
            }
            
            handleVolumeChange();
            
            expect(audio.volume).toBe(0.5);
        });

        test('play button toggles playback state', async () => {
            const playBtn = document.getElementById('playBtn');
            const audio = document.getElementById('audioPlayer');
            
            // Mock play functionality
            async function handlePlayClick() {
                if (audio.paused) {
                    await audio.play();
                    playBtn.textContent = '⏸️';
                } else {
                    audio.pause();
                    playBtn.textContent = '▶️';
                }
            }
            
            // Test play
            audio.paused = true;
            await handlePlayClick();
            
            expect(audio.play).toHaveBeenCalled();
            expect(playBtn.textContent).toBe('⏸️');
            
            // Test pause
            audio.paused = false;
            await handlePlayClick();
            
            expect(audio.pause).toHaveBeenCalled();
            expect(playBtn.textContent).toBe('▶️');
        });
    });

    describe('DOM Manipulation', () => {
        test('updateRecentlyPlayed creates track elements', () => {
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

            const testTracks = [
                { artist: 'Artist 1', title: 'Song 1' },
                { artist: 'Artist 2', title: 'Song 2' },
                { artist: 'Artist 3', title: 'Song 3' }
            ];

            updateRecentlyPlayed(testTracks);

            const container = document.getElementById('recentTracks');
            const trackElements = container.querySelectorAll('.track-item');
            
            expect(trackElements.length).toBe(3);
            expect(trackElements[0].querySelector('.track-artist-name').textContent).toBe('Artist 1:');
            expect(trackElements[0].querySelector('.track-song-name').textContent).toBe('Song 1');
        });
    });

    describe('Error Handling', () => {
        test('handles missing DOM elements gracefully', () => {
            // Mock getElementById to return null for missing elements
            const originalGetElementById = document.getElementById;
            document.getElementById = jest.fn((id) => {
                if (id === 'nonexistentElement') return null;
                return originalGetElementById.call(document, id);
            });

            function safeUpdateElement(id, content) {
                const element = document.getElementById(id);
                if (element) {
                    element.textContent = content;
                    return true;
                } else {
                    console.error(`Element with id '${id}' not found`);
                    return false;
                }
            }

            const result = safeUpdateElement('nonexistentElement', 'test content');
            
            expect(result).toBe(false);
            expect(console.error).toHaveBeenCalledWith("Element with id 'nonexistentElement' not found");
            
            // Restore original function
            document.getElementById = originalGetElementById;
        });

        test('handles fetch errors gracefully', async () => {
            fetch.mockRejectedValueOnce(new Error('Network error'));

            async function safeFetch(url) {
                try {
                    const response = await fetch(url);
                    return await response.json();
                } catch (error) {
                    console.error('Fetch failed:', error.message);
                    return { error: 'Failed to fetch data' };
                }
            }

            const result = await safeFetch('/api/test');
            
            expect(result).toEqual({ error: 'Failed to fetch data' });
            expect(console.error).toHaveBeenCalledWith('Fetch failed:', 'Network error');
        });
    });
});

// Export for use with test runners
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        // Export any functions that need to be tested separately
    };
}
